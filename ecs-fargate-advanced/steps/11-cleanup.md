# Step 11 — Cleanup: Delete All Resources in Correct Order

Resource deletion must follow the correct dependency order. Deleting in the wrong order causes errors (e.g., you cannot delete the VPC until security groups are deleted; you cannot delete the ALB until the service is stopped).

---

## Deletion Order

```
1.  Deregister Auto Scaling policies and scalable target
2.  Delete CloudWatch Alarms
3.  Update Service desired count to 0 (stop all tasks)
4.  Delete ECS Service
5.  Deregister Task Definition
6.  Delete ECS Cluster
7.  Delete ALB Listener
8.  Delete Application Load Balancer
9.  Delete Target Group
10. Delete Security Groups (ecs-sg then alb-sg)
11. Delete ECR Public Repository
12. Delete CloudWatch Log Group
13. Delete CloudWatch Dashboard
14. Delete IAM Roles
15. Delete VPC (subnets, route tables, IGW, VPC)
```

---

## 11.1 Console Cleanup

### Auto Scaling

1. Open **ECS** → **Clusters** → `ECSAdvancedCluster` → **Services** → `ecs-advanced-service`.
2. Click **Update service** → Under **Service Auto Scaling** → disable it.
3. In **CloudWatch** → **Alarms**, delete the two alarms that start with `TargetTracking-service/ECSAdvancedCluster/ecs-advanced-service`. These were created automatically by the target tracking policy.

   > If you used step scaling instead of target tracking, delete `ecs-advanced-cpu-high` and `ecs-advanced-cpu-low`.

### ECS Service and Cluster

1. Go to **ECS** → **Services** → `ecs-advanced-service`.
2. Click **Update service** → set **Desired tasks** to `0` → click **Update**.
3. Wait for all tasks to stop (Tasks tab shows 0 running).
4. Click **Delete service**.
5. Go to **ECS** → **Task definitions** → `ecs-advanced-task` → select revision 1 → **Actions** → **Deregister**.
6. Go to **ECS** → **Clusters** → `ECSAdvancedCluster` → **Delete cluster**.

### Load Balancer

1. Open **EC2** → **Load Balancers** → select `ecs-advanced-alb` → **Actions** → **Delete load balancer**.
2. Open **EC2** → **Target Groups** → select `ecs-advanced-tg` → **Actions** → **Delete**.

### Security Groups

> Delete `ecs-sg` before `alb-sg` (ecs-sg has a reference to alb-sg; delete the dependent first).

1. Open **EC2** → **Security Groups**.
2. Delete `ecs-sg`.
3. Delete `alb-sg`.

### ECR, CloudWatch, IAM

1. **ECR** → **Public registries** → `ecs-advanced-app` → **Delete** → type `delete`.
2. **CloudWatch** → **Log groups** → `/ecs/ecs-advanced-task` → **Delete**.
3. **CloudWatch** → **Dashboards** → `ECSAdvancedDashboard` → **Delete**.
4. **IAM** → **Roles**:
   - Delete `ECSAdvancedTaskExecutionRole`
   - Delete `ECSAdvancedTaskRole`

### VPC (Last)

1. Open **VPC** → **Your VPCs** → select `ecs-advanced-vpc`.
2. First delete all resources in the VPC:
   - **Subnets** → delete `ecs-advanced-public-a` and `ecs-advanced-public-b`
   - **Internet gateways** → select `ecs-advanced-igw` → **Actions** → **Detach** → then **Delete**
   - **Route tables** → delete `ecs-advanced-rt`
3. Return to **Your VPCs** → select `ecs-advanced-vpc` → **Actions** → **Delete VPC**.

---

## 11.2 CLI Cleanup

```bash
# === 1. Remove Auto Scaling ===
aws application-autoscaling delete-scaling-policy \
  --policy-name ecs-advanced-cpu-target-tracking \
  --service-namespace ecs \
  --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
  --scalable-dimension ecs:service:DesiredCount \
  --region us-east-1

aws application-autoscaling deregister-scalable-target \
  --service-namespace ecs \
  --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
  --scalable-dimension ecs:service:DesiredCount \
  --region us-east-1

# === 2. Delete CloudWatch Alarms ===
# Target tracking auto-creates alarms with a TargetTracking- prefix — delete those
# (If you used step scaling, delete ecs-advanced-cpu-high and ecs-advanced-cpu-low instead)
for ALARM in $(aws cloudwatch describe-alarms \
  --alarm-name-prefix "TargetTracking-service/ECSAdvancedCluster/ecs-advanced-service" \
  --query 'MetricAlarms[*].AlarmName' --output text --region us-east-1); do
  aws cloudwatch delete-alarms --alarm-names "$ALARM" --region us-east-1
done

# === 3. Scale service to 0 and delete ===
aws ecs update-service \
  --cluster ECSAdvancedCluster \
  --service ecs-advanced-service \
  --desired-count 0 \
  --region us-east-1

# Wait for tasks to stop
aws ecs wait services-stable \
  --cluster ECSAdvancedCluster \
  --services ecs-advanced-service \
  --region us-east-1

aws ecs delete-service \
  --cluster ECSAdvancedCluster \
  --service ecs-advanced-service \
  --region us-east-1

# === 4. Deregister task definition ===
aws ecs deregister-task-definition \
  --task-definition ecs-advanced-task:1 \
  --region us-east-1

# === 5. Delete ECS cluster ===
aws ecs delete-cluster \
  --cluster ECSAdvancedCluster \
  --region us-east-1

# === 6. Delete ALB (listener is deleted with it) ===
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names ecs-advanced-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text \
  --region us-east-1)

aws elbv2 delete-load-balancer \
  --load-balancer-arn $ALB_ARN \
  --region us-east-1

aws elbv2 wait load-balancers-deleted \
  --load-balancer-arns $ALB_ARN \
  --region us-east-1

# === 7. Delete Target Group ===
TG_ARN=$(aws elbv2 describe-target-groups \
  --names ecs-advanced-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text \
  --region us-east-1)

aws elbv2 delete-target-group \
  --target-group-arn $TG_ARN \
  --region us-east-1

# === 8. Delete Security Groups (ecs-sg first) ===
ECS_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=ecs-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text \
  --region us-east-1)

ALB_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=alb-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text \
  --region us-east-1)

# Fargate task ENIs may take 30–60 seconds to be fully released after service deletion.
# If delete-security-group returns DependencyViolation, wait 30 seconds and retry.
aws ec2 delete-security-group --group-id $ECS_SG --region us-east-1 || \
  (sleep 30 && aws ec2 delete-security-group --group-id $ECS_SG --region us-east-1)

aws ec2 delete-security-group --group-id $ALB_SG --region us-east-1 || \
  (sleep 30 && aws ec2 delete-security-group --group-id $ALB_SG --region us-east-1)

# === 9. Delete ECR repository ===
aws ecr-public delete-repository \
  --repository-name ecs-advanced-app \
  --force \
  --region us-east-1

# === 10. Delete CloudWatch resources ===
aws logs delete-log-group \
  --log-group-name /ecs/ecs-advanced-task \
  --region us-east-1

aws cloudwatch delete-dashboards \
  --dashboard-names ECSAdvancedDashboard \
  --region us-east-1

# === 11. Delete IAM Roles ===
aws iam detach-role-policy \
  --role-name ECSAdvancedTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam delete-role --role-name ECSAdvancedTaskExecutionRole

aws iam delete-role --role-name ECSAdvancedTaskRole

# === 12. Delete VPC resources ===
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=ecs-advanced-vpc" \
  --query 'Vpcs[0].VpcId' \
  --output text \
  --region us-east-1)

# Delete subnets
for SUBNET_ID in $(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[*].SubnetId' \
  --output text \
  --region us-east-1); do
  aws ec2 delete-subnet --subnet-id $SUBNET_ID --region us-east-1
done

# Detach and delete Internet Gateway
IGW_ID=$(aws ec2 describe-internet-gateways \
  --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
  --query 'InternetGateways[0].InternetGatewayId' \
  --output text \
  --region us-east-1)
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region us-east-1
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID --region us-east-1

# Delete non-main route tables
for RT_ID in $(aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'RouteTables[?Associations[0].Main!=`true`].RouteTableId' \
  --output text \
  --region us-east-1); do
  aws ec2 delete-route-table --route-table-id $RT_ID --region us-east-1
done

# Delete the VPC
aws ec2 delete-vpc --vpc-id $VPC_ID --region us-east-1

echo "All resources deleted."
```

---

## 11.3 Final Verification

```bash
# Verify ECS resources are gone
aws ecs list-clusters --region us-east-1
aws ecs list-task-definitions --family-prefix ecs-advanced-task --status ACTIVE --region us-east-1

# Verify ALB is gone
aws elbv2 describe-load-balancers --names ecs-advanced-alb --region us-east-1 2>&1 | grep LoadBalancerNotFound

# Verify VPC is gone
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=ecs-advanced-vpc" --region us-east-1
```

---

## Cleanup Checklist

- [ ] Auto Scaling policies and scalable target deregistered
- [ ] CloudWatch alarms deleted
- [ ] ECS Service deleted (0 tasks running)
- [ ] ECS Task Definition deregistered
- [ ] ECS Cluster deleted
- [ ] ALB and Listener deleted
- [ ] Target Group deleted
- [ ] Security groups `ecs-sg` and `alb-sg` deleted
- [ ] ECR Public repository `ecs-advanced-app` deleted
- [ ] CloudWatch Log Group `/ecs/ecs-advanced-task` deleted
- [ ] CloudWatch Dashboard `ECSAdvancedDashboard` deleted
- [ ] IAM Roles `ECSAdvancedTaskExecutionRole` and `ECSAdvancedTaskRole` deleted
- [ ] VPC `ecs-advanced-vpc` and all sub-resources deleted

---

Congratulations — you have completed **ECS Fargate Advanced**!
