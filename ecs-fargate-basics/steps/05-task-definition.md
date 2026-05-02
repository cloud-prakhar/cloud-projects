# Step 5 — ECS: Register a Task Definition

A **Task Definition** is a JSON blueprint that tells ECS exactly how to run your container:
- Which Docker image to use
- How much CPU and memory to allocate
- Which ports to expose
- Which IAM roles to use
- Where to send logs

---

## 5.1 What You're Creating

```
Task Definition Family:   ecs-basics-task
Launch type:              Fargate
CPU:                      256 (.25 vCPU)
Memory:                   512 MB
Container image:          public.ecr.aws/YOUR_ALIAS/ecs-basics-app:latest
Port:                     5000 (TCP)
Logs:                     CloudWatch Logs → /ecs/ecs-basics-task
Execution Role:           ECSBasicsTaskExecutionRole (from Step 1)
```

---

## 5.2 Console — Register the Task Definition

1. In the ECS Console, click **Task definitions** → **Create new task definition**.
2. Fill in the top section:

   | Field | Value |
   |-------|-------|
   | Task definition family | `ecs-basics-task` |
   | Launch type | **AWS Fargate** |
   | Operating system/Architecture | **Linux/X86_64** |
   | CPU | **0.25 vCPU** |
   | Memory | **0.5 GB** |
   | Task execution role | Select `ECSBasicsTaskExecutionRole` |
   | Task role | None (the app doesn't call AWS APIs) |

3. Scroll to **Container — 1** and click **Add container**:

   | Field | Value |
   |-------|-------|
   | Container name | `ecs-basics-container` |
   | Image URI | `public.ecr.aws/YOUR_ALIAS/ecs-basics-app:latest` |
   | Port mappings | Container port: `5000`, Protocol: `TCP` |
   | Essential | Yes (checked) |

4. Expand **Environment variables** and add:

   | Key | Value |
   |-----|-------|
   | `ENVIRONMENT` | `production` |

5. Expand **Logging** and configure:

   | Field | Value |
   |-------|-------|
   | Log driver | `awslogs` |
   | awslogs-group | `/ecs/ecs-basics-task` |
   | awslogs-region | `us-east-1` |
   | awslogs-stream-prefix | `ecs` |

6. Click **Create**.

---

## 5.3 Pre-create the CloudWatch Log Group

**Do this before registering the Task Definition.** `AmazonECSTaskExecutionRolePolicy` does not include `logs:CreateLogGroup`. If the log group doesn't exist when the task starts, it fails immediately.

```bash
aws logs create-log-group \
  --log-group-name /ecs/ecs-basics-task \
  --region us-east-1
```

> **Console:** Open CloudWatch → Log groups → **Create log group** → name it `/ecs/ecs-basics-task`.

---

## 5.4 AWS CLI — Register the Task Definition

Create a file called `task-definition.json`:

```json
{
  "family": "ecs-basics-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ECSBasicsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "ecs-basics-container",
      "image": "public.ecr.aws/YOUR_ALIAS/ecs-basics-app:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ecs-basics-task",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

> Replace `YOUR_ACCOUNT_ID` and `YOUR_ALIAS` with actual values.

```bash
# Register the task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region us-east-1

# Verify it was registered
aws ecs describe-task-definition \
  --task-definition ecs-basics-task \
  --region us-east-1 \
  --query 'taskDefinition.{Family:family, Revision:revision, Status:status}'
```

---

## 5.5 Understanding CPU and Memory Units

| Console Label | CPU Units | Actual vCPU |
|---------------|-----------|-------------|
| 0.25 vCPU | 256 | Quarter of a CPU core |
| 0.5 vCPU | 512 | Half a CPU core |
| 1 vCPU | 1024 | One full CPU core |

The Flask app in this project uses very little CPU, so 256 units (0.25 vCPU) is sufficient.

---

## 5.6 Understanding Network Mode: awsvpc

Fargate requires `networkMode: awsvpc`. This means:
- Each task gets its **own Elastic Network Interface (ENI)** with a private IP
- If you enable a public IP, the task is directly reachable from the internet
- Security Groups are applied at the ENI level (per task), not at the instance level

---

## Checkpoint

- [ ] CloudWatch log group `/ecs/ecs-basics-task` is created (do this first)
- [ ] Task definition `ecs-basics-task` appears in ECS → Task definitions
- [ ] Status is **ACTIVE**, Revision is 1
- [ ] CPU/Memory shows 0.25 vCPU / 512 MiB
- [ ] Container image URI is correct
- [ ] Execution role is `ECSBasicsTaskExecutionRole`

---

**Next:** [Step 6 — Run the Task and Access the App](./06-run-task.md)
