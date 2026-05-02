# Troubleshooting — ECS Fargate Basics

A reference for every error you're likely to hit during this project.

---

## Error: `ResourceInitializationError: failed to validate logger args`

**Symptom:** Task stops immediately. `stoppedReason` contains:
```
ResourceInitializationError: failed to validate logger args: ... AccessDeniedException:
... is not authorized to perform: logs:CreateLogGroup
```

**Cause:** The CloudWatch log group `/ecs/ecs-basics-task` does not exist, and `AmazonECSTaskExecutionRolePolicy` does **not** grant `logs:CreateLogGroup`. The task fails before the container even starts.

**Fix:** Create the log group manually before running the task:

```bash
aws logs create-log-group \
  --log-group-name /ecs/ecs-basics-task \
  --region us-east-1
```

Then re-run the task. This is covered in Step 5.3 — do not skip it.

---

## Error: Task stuck in PROVISIONING or PENDING state

**Symptom:** The task never reaches RUNNING state. It stays in PROVISIONING for more than 5 minutes.

**Causes and Fixes:**

**1. Docker image URI is incorrect**
- ECS cannot pull the image if the URI has a typo.
- Go to ECS → Task definitions → `ecs-basics-task` → check the image URI.
- Verify the ECR Public alias is correct: `public.ecr.aws/CORRECT_ALIAS/ecs-basics-app:latest`.

**2. Task Execution Role is missing**
- The task has no role to pull the image or write logs.
- In the Task Definition, confirm `executionRoleArn` is set to `ECSBasicsTaskExecutionRole`.

**3. No subnets with internet access**
- Fargate needs to pull the image from ECR Public over the internet.
- Ensure the subnet has a route to an Internet Gateway, or that the task has a public IP.

```bash
# Check task status and failure reason
aws ecs describe-tasks \
  --cluster ECSBasicsCluster \
  --tasks TASK_ARN \
  --region us-east-1 \
  --query 'tasks[0].{Status:lastStatus, Reason:stoppedReason, Containers:containers[*].{Name:name, Reason:reason}}'
```

---

## Error: Task starts then immediately stops (STOPPED)

**Symptom:** The task reaches RUNNING briefly, then stops. `stoppedReason` shows an exit code.

**Cause:** The container process crashed. Flask failed to start.

**Fix:**
1. Check CloudWatch Logs for the task:
   - CloudWatch → Log groups → `/ecs/ecs-basics-task`
   - Open the log stream and read the error.
2. Common causes:
   - Port 5000 already in use (unlikely on Fargate, but possible if the app code has errors)
   - Missing Python dependency (re-build the image and push)
   - `app.py` has a syntax error

```bash
# Get the stopped reason
aws ecs describe-tasks \
  --cluster ECSBasicsCluster \
  --tasks TASK_ARN \
  --region us-east-1 \
  --query 'tasks[0].containers[0].{ExitCode:exitCode, Reason:reason}'
```

---

## Error: Cannot connect to `http://PUBLIC_IP:5000/` (timeout or refused)

**Symptom:** The task is RUNNING but the browser/curl times out.

**Causes:**

**1. Security group does not allow port 5000**
```bash
# Check inbound rules for your security group
aws ec2 describe-security-groups \
  --group-ids SG_ID \
  --region us-east-1 \
  --query 'SecurityGroups[0].IpPermissions'
```
The output should show port 5000 with CIDR `0.0.0.0/0` or your IP.

**Fix:** Add the inbound rule:
```bash
aws ec2 authorize-security-group-ingress \
  --group-id SG_ID \
  --protocol tcp \
  --port 5000 \
  --cidr 0.0.0.0/0 \
  --region us-east-1
```

**2. Task does not have a public IP**
- In ECS task details, check **Network bindings** for a Public IP.
- If none, stop the task and re-run with **Auto-assign public IP: ENABLED**.

**3. Wrong IP or port**
- Confirm the IP is the **Public IP** from the ECS task (not the private IP).
- The app listens on port `5000`, not `80`.

---

## Error: `CannotPullContainerError`

**Symptom:** Task stops immediately. CloudWatch or ECS events show `CannotPullContainerError`.

**Cause:** ECS cannot pull the image from ECR Public.

**Common reasons:**
1. **Image URI typo** — double-check the image URI in your Task Definition.
2. **No internet access** — the Fargate task's subnet has no route to the internet.
3. **Execution role missing ECR permissions** — verify `AmazonECSTaskExecutionRolePolicy` is attached.
4. **Image does not exist** — open ECR Public and confirm the `latest` tag exists.

```bash
# Verify the image exists in ECR Public
aws ecr-public describe-images \
  --repository-name ecs-basics-app \
  --region us-east-1 \
  --query 'imageDetails[*].{Tags:imageTags, PushedAt:imagePushedAt}'
```

---

## Error: `docker push` fails with "no basic auth credentials"

**Symptom:** `docker push` returns `unauthorized: authentication required`.

**Cause:** The ECR Public authentication token expired (valid 12 hours) or you skipped the login step.

**Fix:**
```bash
aws ecr-public get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin public.ecr.aws
```

---

## Error: No logs appear in CloudWatch

**Symptom:** The task ran but `/ecs/ecs-basics-task` log group is empty or missing.

**Causes:**
1. The Task Definition does not have `awslogs` log driver configured.
2. The Execution Role is missing `logs:CreateLogGroup` or `logs:PutLogEvents`.
3. The log group name has a typo — compare the group name in Task Definition vs CloudWatch.

**Fix — Verify log config in Task Definition:**
```bash
aws ecs describe-task-definition \
  --task-definition ecs-basics-task \
  --region us-east-1 \
  --query 'taskDefinition.containerDefinitions[0].logConfiguration'
```

The output should show:
```json
{
  "logDriver": "awslogs",
  "options": {
    "awslogs-group": "/ecs/ecs-basics-task",
    "awslogs-region": "us-east-1",
    "awslogs-stream-prefix": "ecs"
  }
}
```

---

## Error: IAM Role cannot be deleted — "entity in use"

**Symptom:** `aws iam delete-role` fails with `DeleteConflict`.

**Cause:** A policy is still attached to the role, or the role is still referenced by a Task Definition.

**Fix:**
```bash
# First detach all policies
aws iam list-attached-role-policies \
  --role-name ECSBasicsTaskExecutionRole \
  --query 'AttachedPolicies[*].PolicyArn' \
  --output text

# Then detach each one
aws iam detach-role-policy \
  --role-name ECSBasicsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Then delete the role
aws iam delete-role --role-name ECSBasicsTaskExecutionRole
```

---

## General Debugging Checklist

1. Check ECS task's `stoppedReason` in the console or via `describe-tasks`
2. Read CloudWatch Logs — every container stdout line is there
3. Confirm security group has port 5000 open inbound
4. Confirm the task's public IP is set (not just a private IP)
5. Verify the image URI in the Task Definition matches what you pushed to ECR
6. Confirm the Execution Role ARN is attached to the Task Definition
