# Step 5 — ECS: Create the Cluster with Container Insights

You will create an ECS Cluster with **CloudWatch Container Insights** enabled. Container Insights provides CPU, memory, and network metrics per task — which is required for the Auto Scaling policies in Step 9.

---

## 5.1 What You're Creating

```
Cluster Name:              ECSAdvancedCluster
Launch type:               Fargate
Container Insights:        Enabled
Region:                    us-east-1
```

---

## 5.2 Console — Create the Cluster

1. Open the AWS Console → search **Elastic Container Service**.
2. Click **Clusters** → **Create cluster**.
3. Fill in the form:

   | Field | Value |
   |-------|-------|
   | Cluster name | `ECSAdvancedCluster` |
   | Infrastructure | **AWS Fargate (serverless)** |

4. Expand **Monitoring** and **enable CloudWatch Container Insights**.

   > This adds per-task CPU/Memory metrics to CloudWatch under the `ECS/ContainerInsights` namespace. Without this, the Auto Scaling step will not have metrics to act on.

5. Click **Create**.

---

## 5.3 Pre-create the CloudWatch Log Group

`AmazonECSTaskExecutionRolePolicy` does not include `logs:CreateLogGroup`. Create the log group now, before any tasks run:

```bash
aws logs create-log-group \
  --log-group-name /ecs/ecs-advanced-task \
  --region us-east-1
```

> **Console:** CloudWatch → Log groups → **Create log group** → `/ecs/ecs-advanced-task`.

---

## 5.4 CLI — Create the Cluster

```bash
# Create the cluster with Container Insights enabled
aws ecs create-cluster \
  --cluster-name ECSAdvancedCluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1 \
  --settings name=containerInsights,value=enabled \
  --region us-east-1

# Verify
aws ecs describe-clusters \
  --clusters ECSAdvancedCluster \
  --region us-east-1 \
  --query 'clusters[0].{Name:clusterName, Status:status, Settings:settings}'
```

Expected output includes:
```json
{
  "settings": [
    {
      "name": "containerInsights",
      "value": "enabled"
    }
  ]
}
```

---

## 5.5 What Container Insights Provides

| Metric | Description | Used For |
|--------|-------------|----------|
| `CpuUtilized` | vCPU used by each task | Auto Scaling target |
| `MemoryUtilized` | Memory used by each task | Capacity planning |
| `NetworkRxBytes` | Network bytes received | Traffic analysis |
| `NetworkTxBytes` | Network bytes transmitted | Traffic analysis |
| `RunningTaskCount` | Number of running tasks | Service health |

These metrics appear in CloudWatch under:
- **Namespace:** `ECS/ContainerInsights`
- **Dimensions:** `ClusterName`, `ServiceName`, `TaskDefinitionFamily`

---

## Checkpoint

- [ ] CloudWatch log group `/ecs/ecs-advanced-task` created (do this first)
- [ ] Cluster `ECSAdvancedCluster` is **ACTIVE**
- [ ] Container Insights shows **Enabled** in the cluster settings
- [ ] Fargate is listed as a capacity provider

---

**Next:** [Step 6 — Register the Task Definition](./06-task-definition.md)
