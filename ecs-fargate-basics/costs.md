# Cost Guide — ECS Fargate Basics

This guide breaks down every AWS charge you can incur while completing this project. All prices are for **us-east-1** and based on AWS public pricing.

---

## Services Used and Their Pricing Model

| Service | Pricing Model | Free Tier |
|---------|--------------|-----------|
| AWS Fargate | Per vCPU-hour + per GB-hour | 1 month free trial on new accounts only |
| Amazon ECR Public | Free | Always free |
| Amazon CloudWatch Logs | Per GB ingested + per GB stored | 5 GB ingestion/month, 5 GB storage/month |
| Amazon ECS (control plane) | Free | Always free |
| AWS IAM | Free | Always free |
| Amazon VPC / Security Groups | Free | Always free |

---

## Service-by-Service Breakdown

### 1. AWS Fargate

Fargate charges are based on the vCPU and memory allocated to your task — from the moment the task transitions to `RUNNING` until it stops.

**Unit rates (us-east-1, Linux):**

| Resource | Price |
|----------|-------|
| vCPU | $0.04048 per vCPU-hour |
| Memory | $0.004445 per GB-hour |

**This project's configuration:** 1 task × 0.25 vCPU × 0.5 GB

**Cost per hour:**

```
vCPU cost:    0.25 vCPU  × $0.04048/vCPU-hr  = $0.01012/hr
Memory cost:  0.5 GB     × $0.004445/GB-hr    = $0.00222/hr
─────────────────────────────────────────────────────────────
Total:                                           $0.01234/hr
```

**Rounded: ~$0.01 per hour** (about 1 cent per hour)

---

### 2. Amazon ECR Public

| Action | Cost |
|--------|------|
| Push image to ECR Public | Free |
| Pull image from ECR Public | Free |
| Storage in ECR Public | Free |

No charge for this project. ECR Public is completely free for both storage and transfer.

---

### 3. Amazon CloudWatch Logs

| Action | Price | Free Tier |
|--------|-------|-----------|
| Log ingestion | $0.50 per GB | First 5 GB per month |
| Log storage | $0.03 per GB per month | First 5 GB per month |
| Logs Insights queries | $0.005 per GB scanned | First 5 GB per month |

**This project:** The Flask app generates only a few kilobytes of logs (startup message + a handful of HTTP request lines). This is far below the 5 GB free tier — **cost is $0.00**.

---

### 4. Amazon ECS, IAM, VPC

| Service | Cost |
|---------|------|
| ECS cluster (control plane) | Free |
| ECS task scheduling | Free |
| IAM roles and policies | Free |
| VPC, subnets, security groups | Free |

---

## Cost by Scenario

This table shows the Fargate cost for different session lengths. All other services in this project are free.

| Session Length | Tasks | Fargate Cost | Other Services | Total |
|----------------|-------|-------------|----------------|-------|
| 30 minutes | 1 | $0.006 | $0.00 | **$0.01** |
| 1 hour | 1 | $0.012 | $0.00 | **$0.02** |
| 2 hours | 1 | $0.025 | $0.00 | **$0.03** |
| 4 hours | 1 | $0.049 | $0.00 | **$0.05** |
| **Left running 24 hours** ⚠️ | 1 | $0.30 | $0.00 | **$0.30/day** |
| **Left running 7 days** ⚠️ | 1 | $2.07 | $0.00 | **$2.07** |
| **Left running 30 days** ⚠️ | 1 | $8.89 | $0.00 | **$8.89/month** |

> Standalone tasks (not managed by an ECS Service) keep running until you manually stop them. Always complete the [cleanup step](steps/07-cleanup.md).

---

## Formula: Calculate Your Own Cost

If you run the task for a different duration, use this formula:

```
Fargate cost = (vCPU × $0.04048 × hours) + (GB × $0.004445 × hours)

For this project (0.25 vCPU, 0.5 GB):
= (0.25 × $0.04048 × hours) + (0.5 × $0.004445 × hours)
= (0.01012 + 0.00222) × hours
= $0.01234 × hours
```

---

## AWS Free Tier

If this is a **new AWS account** (within the first 12 months), the free tier includes:

| Service | Free Tier Allowance |
|---------|---------------------|
| AWS Fargate | 1 month free trial for new customers: 50 vCPU-hours + 100 GB-memory-hours per month |
| CloudWatch Logs | 5 GB ingestion, 5 GB storage per month (permanent free tier) |
| ECR Public | Always free |

> The Fargate free trial gives you enough to run a 0.25 vCPU task for **200 hours per month at no cost** during the trial period.

---

## Cost-Saving Tips

| Tip | Saving |
|-----|--------|
| **Stop tasks immediately after testing** — standalone tasks keep running | Biggest saving |
| **Use FARGATE_SPOT** instead of FARGATE (see Challenge 6) | ~70% cheaper per hour |
| **Use us-east-1** — it has the lowest Fargate pricing of all regions | ~5–15% vs other regions |
| **Use 0.25 vCPU / 0.5 GB** — minimum size, enough for this app | Minimizes per-hour rate |

---

## What You Will NOT Be Charged For

- The ECS cluster itself (no charge while it has no running tasks)
- ECR Public (always free)
- Security group creation or rules
- IAM roles and policies
- The default VPC
- CloudWatch log group creation
- AWS Management Console usage

---

## Cleanup Reminder

After completing the project, the only resource that still costs money if left running is the **Fargate task**. All other resources (ECS cluster, IAM roles, security group, CloudWatch log group) are either free or have already been deleted.

Run [Step 7 — Cleanup](steps/07-cleanup.md) to stop the task and delete all resources.
