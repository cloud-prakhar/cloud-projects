# Step 4 — ECS: Create a Fargate Cluster

An **ECS Cluster** is a logical grouping of resources where your tasks run. When you use the **Fargate** launch type, you do not provision or manage any EC2 instances — AWS handles all the underlying server infrastructure.

---

## 4.1 What You're Creating

```
Cluster Name:   ECSBasicsCluster
Launch type:    Fargate (serverless — no EC2 instances)
Region:         us-east-1
```

---

## 4.2 Console — Create the Cluster

1. Open the AWS Console and search for **Elastic Container Service (ECS)**.
2. In the left sidebar, click **Clusters** → **Create cluster**.
3. Fill in the form:

   | Field | Value |
   |-------|-------|
   | Cluster name | `ECSBasicsCluster` |
   | Infrastructure | Select **AWS Fargate (serverless)** |

   > Deselect **Amazon EC2 instances** if it appears — you won't need it for Fargate.

4. Under **Monitoring**, you can leave **CloudWatch Container Insights** off for this basic project (it's covered in the advanced project).

5. Click **Create**.

The cluster is created in seconds. You'll see it in **Active** state.

---

## 4.3 AWS CLI (Alternative)

```bash
# Create the ECS cluster with Fargate capacity provider
aws ecs create-cluster \
  --cluster-name ECSBasicsCluster \
  --capacity-providers FARGATE \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1 \
  --region us-east-1

# Verify the cluster was created
aws ecs describe-clusters \
  --clusters ECSBasicsCluster \
  --region us-east-1 \
  --query 'clusters[0].{Name:clusterName, Status:status}'
```

Expected output:
```json
{
    "Name": "ECSBasicsCluster",
    "Status": "ACTIVE"
}
```

---

## 4.4 Understanding ECS Cluster Concepts

| Concept | What It Means |
|---------|--------------|
| **Cluster** | Logical boundary. Your tasks and services run "inside" a cluster. |
| **Capacity Provider** | How compute is sourced. `FARGATE` = serverless. `EC2` = you manage instances. |
| **FARGATE_SPOT** | A cheaper variant of Fargate using spare capacity — can be interrupted. Good for batch jobs. |
| **Service** | Keeps N tasks always running, restarts crashed tasks, integrates with load balancers. |
| **Task** | A single running instance of your container(s). Can be launched standalone or via a Service. |

In this step you are just creating the cluster. The Task Definition (what container to run) comes in Step 5.

---

## Checkpoint

- [ ] Cluster `ECSBasicsCluster` appears in ECS → Clusters
- [ ] Status is **ACTIVE**
- [ ] Infrastructure type shows **Fargate**

---

**Next:** [Step 5 — Register a Task Definition](./05-task-definition.md)
