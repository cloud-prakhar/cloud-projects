# Step 2 — IAM: Roles and Permissions (Full Breakdown)

This project uses **two separate IAM roles**. This step explains exactly what each role does, which permissions it needs, and why.

---

## 2.1 The Two Roles

```
Role 1: ECSAdvancedTaskExecutionRole
  ├── WHO uses it: ECS infrastructure (not your app)
  ├── WHEN used:  At task startup
  └── WHAT it does: Pulls Docker image + writes logs

Role 2: ECSAdvancedTaskRole
  ├── WHO uses it: Your application code (boto3, SDK)
  ├── WHEN used:  While the task is running
  └── WHAT it does: Any AWS API calls your app makes
                    (empty in this project — app calls no AWS APIs)
```

**Why separate them?**
- The Execution Role is infrastructure-level and should never be accessible to application code.
- The Task Role is application-level and should only have what the app specifically needs.
- Mixing them grants application code unnecessary infrastructure permissions.

---

## 2.2 Role 1: Task Execution Role

### Permissions Breakdown

| Permission | AWS Service | Granted By | Why It's Needed |
|------------|-------------|------------|-----------------|
| `ecr:GetAuthorizationToken` | ECR | `AmazonECSTaskExecutionRolePolicy` | Get a short-lived auth token to pull the image |
| `ecr:BatchCheckLayerAvailability` | ECR | `AmazonECSTaskExecutionRolePolicy` | Check if image layers are already cached |
| `ecr:GetDownloadUrlForLayer` | ECR | `AmazonECSTaskExecutionRolePolicy` | Download each layer of the image |
| `ecr:BatchGetImage` | ECR | `AmazonECSTaskExecutionRolePolicy` | Fetch the image manifest |
| `logs:CreateLogStream` | CloudWatch | `AmazonECSTaskExecutionRolePolicy` | Create a per-task log stream |
| `logs:PutLogEvents` | CloudWatch | `AmazonECSTaskExecutionRolePolicy` | Write log lines from the container |

> **Note:** `AmazonECSTaskExecutionRolePolicy` does **not** include `logs:CreateLogGroup`. You must create the CloudWatch log group manually before the service is started (done in Step 5). If the log group is missing, every task will fail immediately with a `ResourceInitializationError`.

### Console — Create the Execution Role

1. Open **IAM** → **Roles** → **Create role**.
2. Trusted entity type: **AWS service**.
3. Use case: **Elastic Container Service Task**.
4. Search for and select `AmazonECSTaskExecutionRolePolicy`.
5. Role name: `ECSAdvancedTaskExecutionRole`.
6. Description: `Execution role for ECS Advanced project — image pull and CloudWatch Logs`.
7. Click **Create role**.

### CLI

```bash
# Create the execution role
aws iam create-role \
  --role-name ECSAdvancedTaskExecutionRole \
  --description "Execution role for ECS Advanced project" \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "ecs-tasks.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach the AWS-managed execution policy
aws iam attach-role-policy \
  --role-name ECSAdvancedTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Save the ARN
EXECUTION_ROLE_ARN=$(aws iam get-role \
  --role-name ECSAdvancedTaskExecutionRole \
  --query 'Role.Arn' \
  --output text)
echo "EXECUTION_ROLE_ARN=$EXECUTION_ROLE_ARN"
```

---

## 2.3 Role 2: Task Role

The Task Role is assumed by your application code. In this project the Flask app does not call any AWS APIs, so this role has **no permissions attached**. It is created as an empty role to show you where application permissions belong.

### When to Add Permissions to the Task Role

| If your app needs to... | Add this policy or permission |
|-------------------------|-------------------------------|
| Read objects from S3 | `s3:GetObject` on the specific bucket ARN |
| Write to DynamoDB | `dynamodb:PutItem`, `dynamodb:GetItem` on the table ARN |
| Read secrets from Secrets Manager | `secretsmanager:GetSecretValue` on the secret ARN |
| Send messages to SQS | `sqs:SendMessage` on the queue ARN |
| Publish to SNS | `sns:Publish` on the topic ARN |

Always use **resource-level ARNs**, never `"Resource": "*"` in production.

### Console — Create the Task Role

1. Open **IAM** → **Roles** → **Create role**.
2. Trusted entity type: **AWS service**.
3. Use case: **Elastic Container Service Task**.
4. Do **not** attach any policies (click through to the name step).
5. Role name: `ECSAdvancedTaskRole`.
6. Description: `Task role for ECS Advanced — attach app-level permissions here`.
7. Click **Create role**.

### CLI

```bash
# Create the task role (no policies attached)
aws iam create-role \
  --role-name ECSAdvancedTaskRole \
  --description "Task role for ECS Advanced project — app-level permissions" \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "ecs-tasks.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'

# Save the ARN
TASK_ROLE_ARN=$(aws iam get-role \
  --role-name ECSAdvancedTaskRole \
  --query 'Role.Arn' \
  --output text)
echo "TASK_ROLE_ARN=$TASK_ROLE_ARN"
```

---

## 2.4 IAM Role Relationship Diagram

```
  ECS Control Plane                   Your Container
  ┌────────────────────┐              ┌──────────────────────────┐
  │  ECS Task Startup  │              │  app.py (Flask)          │
  │                    │              │                          │
  │  Assumes:          │              │  Assumes:                │
  │  ECSAdvanced       │              │  ECSAdvanced             │
  │  TaskExecutionRole │              │  TaskRole                │
  │                    │              │                          │
  │  ↓ Uses to:        │              │  ↓ Uses to call:         │
  │  • Pull ECR image  │              │  • S3, DynamoDB, etc.    │
  │  • Write logs      │              │  (none in this project)  │
  └────────────────────┘              └──────────────────────────┘
```

---

## Checkpoint

- [ ] Role `ECSAdvancedTaskExecutionRole` created with `AmazonECSTaskExecutionRolePolicy`
- [ ] Role `ECSAdvancedTaskRole` created with no policies
- [ ] Both roles have trust principal `ecs-tasks.amazonaws.com`
- [ ] Both Role ARNs are noted/saved

---

**Next:** [Step 3 — Create ECR Public Repository](./03-ecr-public-repo.md)
