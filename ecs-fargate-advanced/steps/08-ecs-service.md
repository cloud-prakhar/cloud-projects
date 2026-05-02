# Step 8 — ECS: Create the Service with ALB Integration

An **ECS Service** keeps a specified number of tasks always running, registers them with the ALB target group, and replaces any task that fails its health check. This is the key difference from a standalone task (Project 1): a Service is self-healing.

---

## 8.1 What You're Creating

```
Service Name:         ecs-advanced-service
Cluster:              ECSAdvancedCluster
Task Definition:      ecs-advanced-task:1
Launch Type:          Fargate
Desired Count:        2 tasks (distributed across 2 AZs)
Load Balancer:        ecs-advanced-alb
Target Group:         ecs-advanced-tg
Container:            ecs-advanced-container:5000
VPC Subnets:          ecs-advanced-public-a, ecs-advanced-public-b
Security Group:       ecs-sg
Public IP:            Enabled (needed to pull ECR image in public subnets)
Deployment Strategy:  Rolling update
```

---

## 8.2 Console — Create the Service

1. Open **ECS** → **Clusters** → `ECSAdvancedCluster`.
2. Click **Services** tab → **Create**.
3. Fill in **Deployment configuration**:

   | Field | Value |
   |-------|-------|
   | Launch type | **FARGATE** |
   | Task definition family | `ecs-advanced-task` |
   | Revision | `1 (latest)` |
   | Service name | `ecs-advanced-service` |
   | Desired tasks | `2` |

4. Under **Deployment options** (expand):

   | Field | Value |
   |-------|-------|
   | Deployment type | **Rolling update** |
   | Minimum healthy percent | `100` |
   | Maximum percent | `200` |

   > **Min 100% / Max 200%** means during a deployment, ECS starts 2 new tasks (200%), then removes 2 old tasks (back to 100%). Zero downtime — old tasks stay up until new ones pass health checks.

5. Under **Networking**:

   | Field | Value |
   |-------|-------|
   | VPC | `ecs-advanced-vpc` |
   | Subnets | Select both `ecs-advanced-public-a` and `ecs-advanced-public-b` |
   | Security group | `ecs-sg` |
   | Public IP | **ENABLED** |

6. Under **Load balancing**:

   | Field | Value |
   |-------|-------|
   | Load balancer type | **Application Load Balancer** |
   | Load balancer | `ecs-advanced-alb` |
   | Container to load balance | `ecs-advanced-container:5000` |
   | Target group | `ecs-advanced-tg` |

7. Click **Create**.

---

## 8.3 CLI

```bash
aws ecs create-service \
  --cluster ECSAdvancedCluster \
  --service-name ecs-advanced-service \
  --task-definition ecs-advanced-task:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[$SUBNET_A,$SUBNET_B],
    securityGroups=[$ECS_SG],
    assignPublicIp=ENABLED
  }" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=ecs-advanced-container,containerPort=5000" \
  --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},minimumHealthyPercent=100,maximumPercent=200" \
  --health-check-grace-period-seconds 60 \
  --region us-east-1
```

> `--health-check-grace-period-seconds 60` gives tasks 60 seconds to start before the ALB begins health checking them. Without this, slow-starting containers can be killed before they're ready.

---

## 8.4 Watch the Service Stabilize

### Console

1. Go to **ECS** → **Clusters** → `ECSAdvancedCluster` → **Services** → `ecs-advanced-service`.
2. Click the **Tasks** tab. You'll see tasks cycle through:
   - `PROVISIONING` → `PENDING` → `RUNNING`
3. Once both tasks are `RUNNING`, check the **Events** tab for:
   ```
   service ecs-advanced-service has reached a steady state.
   ```

### CLI

```bash
# Wait until the service reaches a steady state
aws ecs wait services-stable \
  --cluster ECSAdvancedCluster \
  --services ecs-advanced-service \
  --region us-east-1

echo "Service is stable"

# Check how many tasks are running
aws ecs describe-services \
  --cluster ECSAdvancedCluster \
  --services ecs-advanced-service \
  --region us-east-1 \
  --query 'services[0].{Running:runningCount, Desired:desiredCount, Pending:pendingCount}'
```

---

## 8.5 Test the Application via ALB

```bash
# Replace with your actual ALB DNS name
ALB_DNS="ecs-advanced-alb-XXXXXXXX.us-east-1.elb.amazonaws.com"

# Test the app
curl http://$ALB_DNS/
curl http://$ALB_DNS/health
curl http://$ALB_DNS/info

# Make multiple requests — the container_id will alternate between 2 tasks
for i in {1..6}; do
  curl -s http://$ALB_DNS/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"container_id: {d['container_id']}\")"
done
```

If the ALB is distributing traffic correctly, you should see 2 different `container_id` values alternating in the output. In Fargate with a custom VPC, the hostname format is a long hex string derived from the task ID (e.g., `e8cc5112c5b3475d87588784ff96c27f-3437207229`). This is different from local Docker, where the hostname is a short hex string.

---

## 8.6 Rolling Deployment — How It Works

```
Before deployment:
  [Task A v1] [Task B v1]   (desired=2, running=2)

Start deployment to v2:
  ECS starts new tasks (max 200%):
  [Task A v1] [Task B v1] [Task C v2] [Task D v2]   (4 tasks)

New tasks pass health checks:
  ECS stops old tasks:
  [Task C v2] [Task D v2]   (back to 2)

Zero downtime: the ALB only routes to healthy tasks.
```

To trigger a rolling deployment:
1. Build and push a new image with a new tag (e.g., `v2.1.0`)
2. Register a new Task Definition revision with the updated image URI
3. Update the service: `aws ecs update-service --cluster ECSAdvancedCluster --service ecs-advanced-service --task-definition ecs-advanced-task:2 --region us-east-1`

---

## 8.7 Deployment Circuit Breaker

The CLI command above includes `deploymentCircuitBreaker={enable=true,rollback=true}`. This means:

- If ECS detects that the new deployment is failing (tasks keep crashing), it **automatically rolls back** to the previous task definition revision.
- Without this, a bad deployment stays stuck — tasks keep crashing and restarting indefinitely.

---

## Checkpoint

- [ ] Service `ecs-advanced-service` shows 2 running tasks
- [ ] Service events show "reached a steady state"
- [ ] `curl http://ALB_DNS/` returns a JSON response
- [ ] `curl http://ALB_DNS/health` returns `{"status": "healthy"}`
- [ ] Multiple requests to ALB show different `container_id` values

---

**Next:** [Step 9 — Auto Scaling](./09-auto-scaling.md)
