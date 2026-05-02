# Step 6 — ECS: Register the Task Definition

The Task Definition is the blueprint for your container. In this step you register a production-quality Task Definition with environment variables, a health check, structured logging, and both IAM roles.

---

## 6.1 What You're Creating

```
Family:              ecs-advanced-task
CPU:                 512 (.5 vCPU)
Memory:              1024 MB (1 GB)
Network mode:        awsvpc (required for Fargate)
Execution Role:      ECSAdvancedTaskExecutionRole
Task Role:           ECSAdvancedTaskRole
Container:
  Name:              ecs-advanced-container
  Image:             public.ecr.aws/YOUR_ALIAS/ecs-advanced-app:latest
  Port:              5000 TCP
  Health check:      GET /health → HTTP 200
  Log driver:        awslogs → /ecs/ecs-advanced-task
  Environment vars:  ENVIRONMENT, APP_VERSION, SERVICE_NAME
```

---

## 6.2 Console — Register the Task Definition

1. Open **ECS** → **Task definitions** → **Create new task definition**.
2. Fill in the top section:

   | Field | Value |
   |-------|-------|
   | Task definition family | `ecs-advanced-task` |
   | Launch type | **AWS Fargate** |
   | Operating system/Architecture | **Linux/X86_64** |
   | CPU | **0.5 vCPU** |
   | Memory | **1 GB** |
   | Task execution role | `ECSAdvancedTaskExecutionRole` |
   | Task role | `ECSAdvancedTaskRole` |

3. Scroll to **Container — 1** and click **Add container**:

   | Field | Value |
   |-------|-------|
   | Container name | `ecs-advanced-container` |
   | Image URI | `public.ecr.aws/YOUR_ALIAS/ecs-advanced-app:latest` |
   | Port mappings | Container port: `5000`, Protocol: `TCP`, Name: `flask-port` |
   | Essential | Yes |

4. Expand **Environment variables** and add:

   | Key | Value type | Value |
   |-----|-----------|-------|
   | `ENVIRONMENT` | Value | `production` |
   | `APP_VERSION` | Value | `2.0.0` |
   | `SERVICE_NAME` | Value | `ecs-advanced-app` |

5. Expand **Health check** and configure:

   | Field | Value |
   |-------|-------|
   | Command | `CMD-SHELL, python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" \|\| exit 1` |
   | Interval | `30` seconds |
   | Timeout | `5` seconds |
   | Start period | `15` seconds |
   | Retries | `3` |

   > The **start period** gives the container 15 seconds to initialize before health checks begin. Failing health checks during the start period are not counted.

6. Expand **Logging** and configure:

   | Field | Value |
   |-------|-------|
   | Log driver | `awslogs` |
   | awslogs-group | `/ecs/ecs-advanced-task` |
   | awslogs-region | `us-east-1` |
   | awslogs-stream-prefix | `ecs` |

   > The log group must already exist (created in Step 5). Do not set `awslogs-create-group: true` — the execution role does not have `logs:CreateLogGroup` permission.

7. Click **Create**.

---

## 6.3 CLI — Register via JSON

Create `task-definition.json`:

```json
{
  "family": "ecs-advanced-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ECSAdvancedTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ECSAdvancedTaskRole",
  "containerDefinitions": [
    {
      "name": "ecs-advanced-container",
      "image": "public.ecr.aws/YOUR_ALIAS/ecs-advanced-app:latest",
      "essential": true,
      "portMappings": [
        {
          "name": "flask-port",
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        { "name": "ENVIRONMENT", "value": "production" },
        { "name": "APP_VERSION", "value": "2.0.0" },
        { "name": "SERVICE_NAME", "value": "ecs-advanced-app" }
      ],
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:5000/health')\" || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 15
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ecs-advanced-task",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

> Replace `YOUR_ACCOUNT_ID` with your AWS account ID and `YOUR_ALIAS` with your ECR Public alias.

```bash
# Register the task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region us-east-1

# Verify
aws ecs describe-task-definition \
  --task-definition ecs-advanced-task \
  --region us-east-1 \
  --query 'taskDefinition.{Family:family, Rev:revision, CPU:cpu, Memory:memory, Status:status}'
```

---

## 6.4 Understanding Health Checks

The `healthCheck` block tells ECS whether your container is functioning correctly.

```
container starts
     |
     | (startPeriod: 15s — grace period, failures not counted)
     |
     ↓ first check at 15s
     GET /health → 200 OK? → HEALTHY
     |
     | (interval: 30s between checks)
     |
     ↓ if 3 consecutive failures → UNHEALTHY
     ECS marks the task UNHEALTHY → Service replaces it
```

**Why Python instead of curl?**  
`python:3.12-slim` does not include `curl`. This project uses Python's built-in `urllib.request` for the health check, which is always available. If you want to use `curl` instead, add it in the Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
```

The ALB also performs its own independent health check against `/health` on port 5000 (configured in Step 7). Both the container health check and the ALB health check must pass for a task to receive traffic.

---

## Checkpoint

- [ ] Task definition `ecs-advanced-task` appears in ECS → Task definitions
- [ ] Status is **ACTIVE**, Revision is 1
- [ ] CPU: 0.5 vCPU, Memory: 1 GB
- [ ] Both `ECSAdvancedTaskExecutionRole` and `ECSAdvancedTaskRole` are set
- [ ] Container port 5000 is mapped
- [ ] Log group `/ecs/ecs-advanced-task` is configured
- [ ] 3 environment variables are defined

---

**Next:** [Step 7 — Application Load Balancer and Target Group](./07-alb-target-group.md)
