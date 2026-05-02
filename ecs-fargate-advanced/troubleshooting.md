# Troubleshooting — ECS Fargate Advanced

A comprehensive reference for every error you're likely to hit in this project.

---

## Error: `ResourceInitializationError: failed to validate logger args`

**Symptom:** Task stops immediately. `stoppedReason` contains:
```
ResourceInitializationError: failed to validate logger args: ...
AccessDeniedException: ... not authorized to perform: logs:CreateLogGroup
```

**Cause:** The CloudWatch log group `/ecs/ecs-advanced-task` does not exist. `AmazonECSTaskExecutionRolePolicy` does **not** grant `logs:CreateLogGroup`. The task fails before the container starts.

**Fix:** Create the log group manually (covered in Step 5):
```bash
aws logs create-log-group \
  --log-group-name /ecs/ecs-advanced-task \
  --region us-east-1
```

---

## Error: Tasks start then stop — `stoppedReason: Essential container exited`

**Symptom:** Tasks reach RUNNING briefly, then immediately stop. CloudWatch event shows the essential container exited.

**Diagnosis:**
```bash
aws ecs describe-tasks \
  --cluster ECSAdvancedCluster \
  --tasks TASK_ARN \
  --region us-east-1 \
  --query 'tasks[0].{Status:lastStatus, Reason:stoppedReason, ExitCode:containers[0].exitCode}'
```

**Causes and Fixes:**

| Exit Code | Likely Cause | Fix |
|-----------|-------------|-----|
| `1` | Python exception at startup | Check CloudWatch Logs for the traceback |
| `137` | Container killed (OOM) | Increase memory in Task Definition |
| `143` | SIGTERM (graceful shutdown) | Task was stopped intentionally or health checks failed |

**Read the logs immediately after the stop:**
```bash
LATEST_STREAM=$(aws logs describe-log-streams \
  --log-group-name /ecs/ecs-advanced-task \
  --order-by LastEventTime \
  --descending \
  --query 'logStreams[0].logStreamName' \
  --output text \
  --region us-east-1)

aws logs get-log-events \
  --log-group-name /ecs/ecs-advanced-task \
  --log-stream-name $LATEST_STREAM \
  --region us-east-1 \
  --query 'events[*].message' \
  --output text
```

---

## Error: ALB health checks failing — targets stuck in `unhealthy`

**Symptom:** `aws elbv2 describe-target-health` shows `"State": "unhealthy"`.

**Common reasons:**

**1. Security group `ecs-sg` does not allow traffic from ALB**
```bash
# Verify ecs-sg allows port 5000 from alb-sg
aws ec2 describe-security-groups \
  --group-ids $ECS_SG \
  --region us-east-1 \
  --query 'SecurityGroups[0].IpPermissions'
```
The source should be `alb-sg`'s group ID, not a CIDR.

**Fix:**
```bash
aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG \
  --protocol tcp \
  --port 5000 \
  --source-group $ALB_SG \
  --region us-east-1
```

**2. Health check path is wrong**
- Confirm the target group health check path is `/health` (not `/` or `/healthz`).
- Verify the Flask app returns HTTP 200 on `/health`:
  ```bash
  curl -v http://TASK_IP:5000/health
  ```

**3. Health check grace period too short**
- If tasks are barely starting when the first health check fires, they'll fail.
- Increase `--health-check-grace-period-seconds` in `create-service` to 120.

**4. Wrong port in target group**
- The target group must use port `5000`, matching the container's `EXPOSE 5000`.
- Check: ECS console → Service → Load balancing → confirm port is 5000.

---

## Error: ECS Service stuck in deployment — new tasks not replacing old ones

**Symptom:** Service shows `desiredCount: 2`, but `runningCount` stays at a different number for many minutes. Events tab shows "unable to consistently start tasks successfully."

**Diagnosis:**
```bash
aws ecs describe-services \
  --cluster ECSAdvancedCluster \
  --services ecs-advanced-service \
  --region us-east-1 \
  --query 'services[0].events[:5]'
```

**Causes:**

**1. Deployment circuit breaker triggered**
- ECS detected repeated failures and rolled back.
- Look at the events — if you see "rolling back", check what's failing.

**2. New task definition has a bad image URI**
- Update the task definition to correct the image, then update the service.

**3. Task can't pull the image (CannotPullContainerError)**
- Check if ECR Public has the image: `aws ecr-public describe-images --repository-name ecs-advanced-app --region us-east-1`
- Verify the Execution Role has `AmazonECSTaskExecutionRolePolicy` attached.

---

## Error: `Service cannot be created because the cluster does not exist`

**Symptom:** `create-service` CLI call fails with the above message.

**Cause:** You're using the wrong cluster name or wrong region.

**Fix:**
```bash
# List your clusters
aws ecs list-clusters --region us-east-1

# Verify the cluster name is exactly ECSAdvancedCluster
```

---

## Error: ALB returns 502 Bad Gateway

**Symptom:** `curl http://ALB_DNS/` returns HTTP 502.

**What 502 means:** The ALB reached a target, but the target returned an error or closed the connection unexpectedly.

**Causes:**

**1. Flask app is not running on the expected port**
- Verify the app listens on `0.0.0.0:5000` (not `127.0.0.1:5000`).
- In `app.py`, ensure: `app.run(host="0.0.0.0", port=port)`.
- Binding to `127.0.0.1` only works for local connections — the ALB connects from a different IP.

**2. No healthy targets in the target group**
- Run `describe-target-health` and confirm at least one target is healthy.

**3. Container started but crashed after passing the initial health check**
- Read the most recent CloudWatch Logs for any uncaught exceptions.

---

## Error: ALB returns 503 Service Unavailable

**Symptom:** `curl http://ALB_DNS/` returns HTTP 503.

**What 503 means:** No healthy targets are registered in the target group.

**Causes:**
- All tasks are in `PENDING` or `STOPPED` state — none are healthy yet.
- Wait 60–90 seconds for tasks to start and pass health checks.
- If it persists, check task status and health check configuration.

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --region us-east-1

# Check running task count
aws ecs describe-services \
  --cluster ECSAdvancedCluster \
  --services ecs-advanced-service \
  --region us-east-1 \
  --query 'services[0].{Running:runningCount, Desired:desiredCount}'
```

---

## Error: VPC deletion fails — `DependencyViolation`

**Symptom:** `aws ec2 delete-vpc` fails with `DependencyViolation: The vpc has dependencies and cannot be deleted`.

**Cause:** Resources inside the VPC were not fully deleted before attempting to delete the VPC.

**Fix — find and remove dependencies:**
```bash
# Find network interfaces still attached
aws ec2 describe-network-interfaces \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --region us-east-1 \
  --query 'NetworkInterfaces[*].{ID:NetworkInterfaceId, Status:Status, Description:Description}'

# If there are ENIs from the ALB, wait 2-3 minutes after ALB deletion for them to be released
# Then retry the VPC deletion
```

---

## Error: Security group cannot be deleted — `InvalidGroup.InUse`

**Symptom:** Deleting `alb-sg` fails because `ecs-sg` references it as a source in an inbound rule.

**Cause:** `ecs-sg` has an inbound rule with source = `alb-sg`. You must delete or modify `ecs-sg` before deleting `alb-sg`.

**Fix:** Always delete `ecs-sg` before `alb-sg`:
```bash
aws ec2 delete-security-group --group-id $ECS_SG --region us-east-1
aws ec2 delete-security-group --group-id $ALB_SG --region us-east-1
```

---

## Error: Security group deletion fails with `DependencyViolation` after service deletion

**Symptom:** `delete-security-group` fails for `ecs-sg` with:
```
DependencyViolation: resource sg-XXXX has a dependent object
```
Even though the ECS service and all tasks have been stopped.

**Cause:** Fargate tasks use ENIs that are attached to the security group. After the service is deleted, these ENIs go into `available` state but take 30–60 seconds to be fully released by the ECS control plane.

**Fix:** Wait 30–60 seconds after deleting the service and the ALB, then retry:
```bash
sleep 60
aws ec2 delete-security-group --group-id $ECS_SG --region us-east-1
aws ec2 delete-security-group --group-id $ALB_SG --region us-east-1
```

You can check if the ENIs are still present:
```bash
aws ec2 describe-network-interfaces \
  --filters "Name=group-id,Values=$ECS_SG" \
  --query 'NetworkInterfaces[*].{ID:NetworkInterfaceId, Status:Status}' \
  --region us-east-1
```
When the result is empty `[]`, the security group can be deleted.

---

## Error: Auto Scaling does not trigger

**Symptom:** CPU is clearly above 60% but no new tasks are launched.

**Causes:**

**1. Container Insights is not enabled on the cluster**
- Without Container Insights, the `ECS/ContainerInsights` namespace has no data.
- Fix: enable it in the cluster settings and wait 5 minutes for data to appear.

**2. CloudWatch alarm is in INSUFFICIENT_DATA state**
```bash
aws cloudwatch describe-alarms \
  --alarm-names ecs-advanced-cpu-high \
  --region us-east-1 \
  --query 'MetricAlarms[0].StateValue'
```
If `INSUFFICIENT_DATA`, Container Insights metrics haven't emitted yet. Wait 5 minutes and check again.

**3. Already at max capacity**
- The scalable target has `maxCapacity: 4`. If you already have 4 tasks, no more will be added.

---

## General Debugging Checklist

1. Check `describe-tasks` for `stoppedReason` and container exit codes
2. Read CloudWatch Logs for the application traceback
3. Run `describe-target-health` to confirm ALB targets are healthy
4. Verify security group rules allow port 5000 from `alb-sg` to `ecs-sg`
5. Confirm Flask binds to `0.0.0.0`, not `127.0.0.1`
6. Check the ECS Service **Events** tab for deployment state messages
7. Verify both IAM roles are attached to the Task Definition
8. Confirm the image URI in the Task Definition matches what was pushed to ECR
