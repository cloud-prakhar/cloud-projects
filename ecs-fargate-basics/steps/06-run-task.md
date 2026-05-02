# Step 6 — ECS: Run the Task and Access the App

You will now launch the task inside your ECS Cluster and access the running Flask application over the internet.

---

## 6.1 What Happens When You Run a Task

```
You click "Run Task"
        ↓
ECS allocates Fargate capacity (new container environment)
        ↓
ECS assumes the Task Execution Role → pulls image from ECR Public
        ↓
Container starts → Flask app listens on port 5000
        ↓
ECS assigns a public IP to the task's ENI (if enabled)
        ↓
You access http://PUBLIC_IP:5000/
```

---

## 6.2 Console — Run the Task

1. In the ECS Console, open **Clusters** → `ECSBasicsCluster`.
2. Click the **Tasks** tab → **Run new task**.
3. Fill in the form:

   | Field | Value |
   |-------|-------|
   | Launch type | **FARGATE** |
   | Platform version | **LATEST** |
   | Task definition family | `ecs-basics-task` |
   | Revision | `1 (latest)` |
   | Number of tasks | `1` |

4. Under **Networking**:

   | Field | Value |
   |-------|-------|
   | VPC | Select the **default VPC** |
   | Subnets | Select any 1 or 2 subnets |
   | Security group | Create a new one (see below) |
   | Public IP | **ENABLED** |

5. **Create a new security group:**

   | Rule | Value |
   |------|-------|
   | Type | Custom TCP |
   | Port range | 5000 |
   | Source | My IP (or `0.0.0.0/0` for any) |
   | Description | Allow inbound to Flask on port 5000 |

   > `0.0.0.0/0` allows access from anywhere. For a learning project this is fine, but restrict to your IP in production.

6. Click **Create** (or **Run**).

---

## 6.3 Wait for the Task to Start

The task starts in **PROVISIONING** state, then **PENDING**, then **RUNNING**.

1. In the **Tasks** tab, click the task ID to open its details.
2. Wait until **Last status** shows **RUNNING** (typically 30–60 seconds).
3. Under **Network bindings** → find the **Public IP**.

   > If you don't see a Public IP: the subnet does not auto-assign public IPs, or you disabled the Public IP option. Go back and re-run with Public IP enabled.

---

## 6.4 Access the Application

Once the task is **RUNNING** and you have the Public IP:

```bash
# Replace PUBLIC_IP with the actual IP from the ECS console
curl http://PUBLIC_IP:5000/

# Test the health endpoint
curl http://PUBLIC_IP:5000/health
```

Or open in your browser:
```
http://PUBLIC_IP:5000/
```

Expected response:
```json
{
  "container_id": "ip-172-31-11-225.ec2.internal",
  "environment": "production",
  "message": "Hello from ECS Fargate!",
  "version": "1.0.0"
}
```

The `container_id` is the container's hostname. In Fargate using the default VPC, this is the **internal DNS name** of the task's private IP (e.g., `ip-172-31-11-225.ec2.internal`). In a custom VPC, it is a longer hex string derived from the task ID. This is different from local Docker, where the hostname is a short hex string.

---

## 6.5 View Container Logs in CloudWatch

The Flask app writes output to stdout, which ECS forwards to CloudWatch Logs automatically.

1. Open **CloudWatch** in the AWS Console.
2. Click **Log groups** → `/ecs/ecs-basics-task`.
3. Click the log stream (named like `ecs/ecs-basics-container/TASK_ID`).
4. You'll see the Flask startup message and any request logs.

### CLI — Tail the Logs

```bash
# List log streams in the group
aws logs describe-log-streams \
  --log-group-name /ecs/ecs-basics-task \
  --region us-east-1 \
  --order-by LastEventTime \
  --descending \
  --query 'logStreams[0].logStreamName' \
  --output text

# Read log events from the most recent stream
# Replace LOG_STREAM_NAME with the value from above
aws logs get-log-events \
  --log-group-name /ecs/ecs-basics-task \
  --log-stream-name LOG_STREAM_NAME \
  --region us-east-1 \
  --query 'events[*].message' \
  --output text
```

---

## 6.6 AWS CLI — Run the Task

If you prefer to run the task from the CLI:

```bash
# First get your default VPC ID
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=is-default,Values=true" \
  --query 'Vpcs[0].VpcId' \
  --output text \
  --region us-east-1)

# Get a subnet ID from the default VPC
SUBNET_ID=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[0].SubnetId' \
  --output text \
  --region us-east-1)

# Create a security group allowing inbound on port 5000
SG_ID=$(aws ec2 create-security-group \
  --group-name ecs-basics-sg \
  --description "Allow port 5000 for ECS Basics task" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text \
  --region us-east-1)

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5000 \
  --cidr 0.0.0.0/0 \
  --region us-east-1

# Run the task
TASK_ARN=$(aws ecs run-task \
  --cluster ECSBasicsCluster \
  --task-definition ecs-basics-task:1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region us-east-1 \
  --query 'tasks[0].taskArn' \
  --output text)

echo "Task ARN: $TASK_ARN"

# Wait for the task to reach RUNNING state
aws ecs wait tasks-running \
  --cluster ECSBasicsCluster \
  --tasks $TASK_ARN \
  --region us-east-1

echo "Task is RUNNING"

# Get the public IP of the task's network interface
ENI_ID=$(aws ecs describe-tasks \
  --cluster ECSBasicsCluster \
  --tasks $TASK_ARN \
  --region us-east-1 \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text)

PUBLIC_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids $ENI_ID \
  --region us-east-1 \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text)

echo "App running at: http://$PUBLIC_IP:5000/"
```

---

## Checkpoint

- [ ] Task status is **RUNNING** in ECS → Clusters → ECSBasicsCluster → Tasks
- [ ] You can access `http://PUBLIC_IP:5000/` and get a JSON response
- [ ] Log events appear in CloudWatch → `/ecs/ecs-basics-task`
- [ ] The `container_id` in the response is a short hex string (the container hostname)

---

**Next:** [Step 7 — Cleanup](./07-cleanup.md)
