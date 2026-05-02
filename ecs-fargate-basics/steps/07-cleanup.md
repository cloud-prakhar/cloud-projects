# Step 7 — Cleanup: Delete All Resources

Delete all resources created in this project. Follow the order below — some resources depend on others and cannot be deleted until the dependents are removed first.

---

## Cleanup Order

```
1. Stop running ECS task
2. Delete ECS Task Definition (deregister)
3. Delete ECS Cluster
4. Delete Security Group
5. Delete ECR Public repository
6. Delete CloudWatch Log Group
7. Delete IAM Role
```

---

## 7.1 Console Cleanup

### Stop the ECS Task

1. Open **ECS** → **Clusters** → `ECSBasicsCluster` → **Tasks** tab.
2. Select the running task and click **Stop**.
3. Confirm the stop action.

### Deregister the Task Definition

1. Open **ECS** → **Task definitions** → `ecs-basics-task`.
2. Select revision `1`.
3. Click **Actions** → **Deregister**.

> Deregistered task definitions remain visible but cannot be used to launch new tasks.

### Delete the ECS Cluster

1. Open **ECS** → **Clusters**.
2. Select `ECSBasicsCluster` and click **Delete cluster**.
3. Type the cluster name to confirm and click **Delete**.

### Delete the Security Group

1. Open **EC2** → **Security Groups**.
2. Find `ecs-basics-sg`.
3. Select it → **Actions** → **Delete security groups**.

### Delete the ECR Public Repository

1. Open **ECR** → **Public registries**.
2. Select `ecs-basics-app` and click **Delete**.
3. Type `delete` to confirm.

### Delete the CloudWatch Log Group

1. Open **CloudWatch** → **Log groups**.
2. Select `/ecs/ecs-basics-task` and click **Actions** → **Delete log group(s)**.

### Delete the IAM Role

1. Open **IAM** → **Roles**.
2. Search for `ECSBasicsTaskExecutionRole`.
3. Click the role → **Delete** → type the role name → confirm.

---

## 7.2 AWS CLI Cleanup

```bash
# 1. Stop the running task (replace TASK_ARN with your actual task ARN)
aws ecs stop-task \
  --cluster ECSBasicsCluster \
  --task TASK_ARN \
  --region us-east-1

# 2. Deregister the task definition
aws ecs deregister-task-definition \
  --task-definition ecs-basics-task:1 \
  --region us-east-1

# 3. Delete the ECS cluster
aws ecs delete-cluster \
  --cluster ECSBasicsCluster \
  --region us-east-1

# 4. Delete the security group (replace SG_ID with your actual SG ID)
aws ec2 delete-security-group \
  --group-id SG_ID \
  --region us-east-1

# 5. Delete the ECR Public repository (delete-repository removes images too)
aws ecr-public delete-repository \
  --repository-name ecs-basics-app \
  --force \
  --region us-east-1

# 6. Delete the CloudWatch log group
aws logs delete-log-group \
  --log-group-name /ecs/ecs-basics-task \
  --region us-east-1

# 7. Detach policy from IAM role before deleting
aws iam detach-role-policy \
  --role-name ECSBasicsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam delete-role \
  --role-name ECSBasicsTaskExecutionRole
```

---

## 7.3 Verify Everything Is Deleted

```bash
# Check no ECS clusters remain
aws ecs list-clusters --region us-east-1

# Check no task definitions remain active
aws ecs list-task-definitions \
  --family-prefix ecs-basics-task \
  --status ACTIVE \
  --region us-east-1

# Check no log group remains
aws logs describe-log-groups \
  --log-group-name-prefix /ecs/ecs-basics-task \
  --region us-east-1

# Check the IAM role is gone
aws iam get-role --role-name ECSBasicsTaskExecutionRole 2>&1 | grep NoSuchEntity
```

---

## Checkpoint

- [ ] No tasks running in `ECSBasicsCluster`
- [ ] `ECSBasicsCluster` is deleted
- [ ] `ecs-basics-task` task definition is deregistered
- [ ] `ecs-basics-sg` security group is deleted
- [ ] ECR Public repository `ecs-basics-app` is deleted
- [ ] CloudWatch log group `/ecs/ecs-basics-task` is deleted
- [ ] IAM role `ECSBasicsTaskExecutionRole` is deleted

---

Congratulations — you have completed **ECS Fargate Basics**!

**Ready for more?** Continue to [ECS Fargate Advanced](../../ecs-fargate-advanced/README.md).
