# Step 1 — IAM: Create the ECS Task Execution Role

ECS Fargate needs an IAM role to perform two things on your behalf:
1. **Pull your Docker image** from ECR
2. **Write container logs** to CloudWatch Logs

This role is called the **Task Execution Role**. It is used by the ECS infrastructure, not by your application code.

---

## 1.1 What You're Creating

```
Role Name:  ECSBasicsTaskExecutionRole
Trust:      ecs-tasks.amazonaws.com  (ECS can assume this role)
Policy:     AmazonECSTaskExecutionRolePolicy  (managed by AWS)
```

The managed policy `AmazonECSTaskExecutionRolePolicy` grants exactly:
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:GetDownloadUrlForLayer`
- `ecr:BatchGetImage`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

> **Important:** This policy does **not** include `logs:CreateLogGroup`. You must create the CloudWatch log group manually before running the task (done in Step 5). If the log group does not exist, the task will fail immediately with a `ResourceInitializationError`.

---

## 1.2 Console — Create the Role

1. Open the [AWS Console](https://console.aws.amazon.com) and search for **IAM**.
2. In the left sidebar, click **Roles** → **Create role**.
3. Under **Trusted entity type**, choose **AWS service**.
4. Under **Use case**, scroll to **Elastic Container Service** and select **Elastic Container Service Task**.

   > This is important: selecting "Task" (not just "ECS") sets the trust principal to `ecs-tasks.amazonaws.com`.

5. Click **Next**.
6. In the search box, type `AmazonECSTaskExecutionRolePolicy` and select the checkbox.
7. Click **Next**.
8. Set the role name to `ECSBasicsTaskExecutionRole`.
9. Click **Create role**.

---

## 1.3 Console — Verify the Role

1. Click into the newly created role.
2. Confirm the **Trust relationships** tab shows:
   ```json
   {
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "Statement1",
			"Effect": "Allow",
			"Principal": {
				"Service": "ecs-tasks.amazonaws.com"
			},
			"Action": "sts:AssumeRole"
		}
	]
}
```
3. Confirm **Permissions** tab shows `AmazonECSTaskExecutionRolePolicy`.
4. Copy the **ARN** from the top — you will need it in Step 5.

---

## 1.4 AWS CLI (Alternative)

```bash
# Step 1: Create the role with the correct trust policy
aws iam create-role \
  --role-name ECSBasicsTaskExecutionRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "ecs-tasks.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Step 2: Attach the AWS-managed execution policy
aws iam attach-role-policy \
  --role-name ECSBasicsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Step 3: Get the role ARN (save this for Step 5)
aws iam get-role \
  --role-name ECSBasicsTaskExecutionRole \
  --query 'Role.Arn' \
  --output text
```

---

## Checkpoint

- [ ] Role `ECSBasicsTaskExecutionRole` exists in IAM → Roles
- [ ] Trusted entity is `ecs-tasks.amazonaws.com`
- [ ] Policy `AmazonECSTaskExecutionRolePolicy` is attached
- [ ] You have the Role ARN copied (format: `arn:aws:iam::ACCOUNT_ID:role/ECSBasicsTaskExecutionRole`)

---

**Next:** [Step 2 — Create an ECR Public Repository](./02-ecr-public-repo.md)
