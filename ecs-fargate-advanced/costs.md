# Cost Guide — ECS Fargate Advanced

This guide breaks down every AWS charge you can incur while completing this project. All prices are for **us-east-1** and based on AWS public pricing.

---

## Services Used and Their Pricing Model

| Service | Pricing Model | Free Tier |
|---------|--------------|-----------|
| AWS Fargate | Per vCPU-hour + per GB-hour | 1-month trial for new accounts |
| Application Load Balancer | Per ALB-hour + per LCU-hour | 750 hours/month for 12 months (new accounts) |
| Amazon ECR Public | Free | Always free |
| Amazon CloudWatch Logs | Per GB ingested + per GB stored | 5 GB ingestion/month, 5 GB storage/month |
| CloudWatch Container Insights | Per GB of metrics ingested | None |
| Application Auto Scaling | Free | Always free |
| Amazon ECS (control plane) | Free | Always free |
| Amazon VPC / IGW / Subnets | Free | Always free |
| AWS IAM | Free | Always free |

---

## Service-by-Service Breakdown

### 1. AWS Fargate

Fargate charges start when a task transitions to `RUNNING` and stop when the task stops.

**Unit rates (us-east-1, Linux):**

| Resource | Price |
|----------|-------|
| vCPU | $0.04048 per vCPU-hour |
| Memory | $0.004445 per GB-hour |

**This project's configuration:** 2 tasks × 0.5 vCPU × 1 GB

**Cost per hour (2 tasks running):**

```
Per task:
  vCPU:   0.5 vCPU × $0.04048/vCPU-hr  = $0.02024/hr
  Memory: 1.0 GB   × $0.004445/GB-hr    = $0.00445/hr
  ─────────────────────────────────────────────────────
  Per task total:                          $0.02469/hr

2 tasks:  $0.02469 × 2                  = $0.04937/hr
```

**Rounded: ~$0.05 per hour** for 2 tasks

**If Auto Scaling triggers and you reach 4 tasks:**

```
4 tasks:  $0.02469 × 4 = $0.09874/hr  ≈ $0.10/hr
```

---

### 2. Application Load Balancer (ALB)

ALB charges have two components: a fixed hourly charge plus a usage-based charge.

**Unit rates:**

| Component | Price | What It Covers |
|-----------|-------|----------------|
| ALB-hour | $0.008 per hour | Fixed charge — applies even with zero traffic |
| LCU-hour | $0.008 per LCU-hour | Usage-based — 1 LCU = 1 new connection/sec OR 25 active connections OR 1 GB/hr |

**This project:**
- Fixed charge: $0.008 per hour
- LCU charge: Negligible for learning-volume traffic (~5–10 test requests). Well under 1 LCU/hour.
- **Effective cost: ~$0.008/hr = about 0.8 cents per hour**

> **Key fact:** The ALB charges by the hour regardless of whether it receives any traffic. This is the most important resource to delete promptly after completing the project.

---

### 3. Amazon ECR Public

| Action | Cost |
|--------|------|
| Push image | Free |
| Pull image | Free |
| Storage | Free |

No charges for this project.

---

### 4. Amazon CloudWatch Logs

| Action | Price | Free Tier |
|--------|-------|-----------|
| Log ingestion | $0.50 per GB | First 5 GB per month |
| Log storage | $0.03 per GB per month | First 5 GB per month |
| Logs Insights queries | $0.005 per GB scanned | First 5 GB per month |

**This project:** Two tasks generate a few kilobytes of logs. Log Insights queries scan only that tiny volume. Both are far below the 5 GB free tier — **cost is $0.00**.

---

### 5. CloudWatch Container Insights

Container Insights is enabled on the cluster (Step 5). It publishes CPU, memory, and network metrics for each task. These are **not part of the CloudWatch standard free tier**.

**Pricing:**

| Component | Price |
|-----------|-------|
| Metrics ingestion | $0.35 per GB of metric data |

**How much data does Container Insights generate?**

Each running task publishes metrics roughly every 60 seconds. With 2 tasks, the data volume is approximately:

```
~2 tasks × ~3 KB per metric flush × 60 flushes per hour = ~360 KB/hr
For a 4-hour session: ~1.44 MB total = 0.00144 GB
Cost: 0.00144 GB × $0.35/GB = $0.0005
```

**Rounded: less than $0.01 for this project.** Essentially free at learning scale.

> For production clusters running dozens of tasks 24/7, Container Insights costs scale meaningfully — budget for it before enabling in production.

---

### 6. Application Auto Scaling

Free. There is no charge for registering scalable targets or creating scaling policies.

The CloudWatch alarms that target tracking creates are also free — standard CloudWatch alarms are priced at $0.10 per alarm per month, but AWS does not charge for the alarms auto-created by Application Auto Scaling.

---

### 7. Amazon VPC and Networking

| Resource | Cost |
|----------|------|
| VPC | Free |
| Subnets | Free |
| Internet Gateway | Free |
| Route tables | Free |
| Security groups | Free |
| Data transfer out to internet | First 100 GB/month free, then $0.09/GB |

For this project (a handful of test requests totaling a few KB), data transfer is effectively free.

> **What we are NOT using:** NAT Gateway. If we moved ECS tasks to private subnets (Challenge 2), we would need a NAT Gateway at $0.045/hr + $0.045/GB — roughly $32/month fixed cost. This is why the project deliberately uses public subnets to keep learning costs minimal.

---

## Cost by Scenario

All scenarios below assume 2 Fargate tasks running (the project's default desired count).

| Session Length | Fargate (2 tasks) | ALB | Container Insights | Total |
|----------------|------------------|-----|--------------------|-------|
| 1 hour | $0.05 | $0.008 | < $0.001 | **~$0.06** |
| 2 hours | $0.10 | $0.016 | < $0.001 | **~$0.12** |
| 4 hours (typical) | $0.20 | $0.032 | < $0.001 | **~$0.24** |
| 8 hours | $0.40 | $0.064 | $0.002 | **~$0.47** |
| **Left running 24 hours** ⚠️ | $1.18 | $0.19 | $0.006 | **~$1.38/day** |
| **Left running 7 days** ⚠️ | $8.29 | $1.34 | $0.04 | **~$9.67** |
| **Left running 30 days** ⚠️ | $35.55 | $5.76 | $0.18 | **~$41.49/month** |

> ⚠️ The ALB charges by the hour even with zero requests. If you forget to delete it, it costs ~$5.76 per month regardless of traffic. Always run [Step 11 — Cleanup](steps/11-cleanup.md).

---

## Hourly Cost Breakdown (Visual)

```
Per hour with 2 tasks running:

  Fargate (2 tasks)     ████████████████████████████  $0.0494  (~82%)
  ALB (fixed)           █████                         $0.0080  (~13%)
  Container Insights    ░                             $0.0001  (~0.2%)
  Everything else       —                             $0.0000
  ──────────────────────────────────────────────────────────────────
  Total per hour                                      ~$0.057
```

---

## Formula: Calculate Your Own Cost

```
Fargate cost  = (vCPU × $0.04048 + GB × $0.004445) × tasks × hours
ALB cost      = $0.008 × hours  (+ LCU cost, negligible for test traffic)

For this project (0.5 vCPU, 1 GB, 2 tasks):
Fargate/hr = (0.5 × $0.04048 + 1.0 × $0.004445) × 2 = $0.04937
ALB/hr     = $0.008
─────────────────────────────────────────────────────────────────
Total/hr   ≈ $0.057

For N hours:  $0.057 × N
```

---

## AWS Free Tier

If this is a **new AWS account** (within the first 12 months):

| Service | Free Tier Allowance |
|---------|---------------------|
| AWS Fargate | 1-month trial: 50 vCPU-hours + 100 GB-memory-hours per month |
| Application Load Balancer | 750 ALB-hours per month for 12 months |
| CloudWatch Logs | 5 GB ingestion, 5 GB storage per month (permanent) |

**Under the free tier, this project costs $0.00** for a typical 4-hour learning session:
- Fargate: 2 tasks × 0.5 vCPU × 4 hours = 4 vCPU-hours → within 50 vCPU-hour free tier
- ALB: 4 hours → within 750 ALB-hour free tier
- Logs and Insights: within free tier or negligible

> Container Insights has no free tier. Its cost for this project (~$0.001) applies even on new accounts, but it rounds to $0.00 on your bill.

---

## Fargate vs Fargate Spot

If you complete Challenge 1 (scheduled scaling) or just want to reduce Fargate cost:

| | Fargate | Fargate Spot |
|-|---------|--------------|
| vCPU price/hr | $0.04048 | ~$0.01219 (~70% cheaper) |
| Memory price/hr | $0.004445 | ~$0.00133 (~70% cheaper) |
| Interruption risk | None | Can be interrupted with 2-min notice |
| Best for | Long-running services | Batch jobs, fault-tolerant workloads |

**With Fargate Spot (2 tasks, 4 hours):**

```
Fargate Spot = (0.5 × $0.01219 + 1.0 × $0.00133) × 2 tasks × 4 hrs ≈ $0.06
vs regular   = $0.20
Saving       = ~70%
```

---

## Cost-Saving Tips

| Tip | Impact |
|-----|--------|
| **Delete the ALB immediately after testing** — it charges $0.008/hr with zero traffic | High |
| **Scale the ECS Service to 0 before deleting** — stops Fargate charges instantly | High |
| **Use FARGATE_SPOT for non-critical workloads** — ~70% cheaper | Medium |
| **Disable Container Insights if not needed** — saves $0.35/GB in metrics | Low (at learning scale) |
| **Do not create a NAT Gateway** — not needed for this project's public subnet setup | Saves ~$32/month |
| **Use us-east-1** — lowest Fargate and ALB pricing | Low (~5–15% vs other regions) |

---

## What You Will NOT Be Charged For

- ECS cluster control plane
- ECS service scheduling and task placement
- VPC, subnets, Internet Gateway, route tables
- Security groups and their rules
- IAM roles and policies
- ECR Public storage and pull
- Application Auto Scaling (policies and scalable targets)
- CloudWatch alarm creation (including alarms auto-created by target tracking)
- AWS Management Console usage

---

## Cleanup Reminder

Resources that cost money if left running:

| Resource | Hourly Cost | Action |
|----------|-------------|--------|
| Fargate tasks (2) | ~$0.049/hr | Set service desired count to 0, then delete service |
| Application Load Balancer | $0.008/hr | Delete load balancer |

Everything else in this project is free or pay-per-use with zero ongoing cost once the tasks stop.

Run [Step 11 — Cleanup](steps/11-cleanup.md) to delete all resources in the correct order.
