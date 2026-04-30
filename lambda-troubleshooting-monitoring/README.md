# Lambda Troubleshooting, Monitoring & Boto3 Automation

## What You'll Build

The most comprehensive project in the series. You'll:

1. Deploy a **multi-scenario buggy Lambda function** that intentionally fails in different ways
2. Use **CloudWatch Logs** to diagnose each failure from raw log events
3. Write **CloudWatch Log Insights queries** to filter, aggregate, and analyse log data
4. Configure a **Dead-Letter Queue (DLQ)** to capture async invocation failures
5. Deploy three production-pattern Lambda functions that automate **EC2**, **S3**, and **SQS** operations via Boto3
6. Run a local **Boto3 management script** that invokes scenarios, queries logs, and reports metrics

---

## Architecture

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │                        BuggyLambda                                    │
  │  scenario=ok | unhandled_error | timeout | memory_oom | ...          │
  └─────────────────────────────┬────────────────────────────────────────┘
                                │ writes logs
                                ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │             /aws/lambda/BuggyLambda  (CloudWatch Log Group)          │
  │                                                                        │
  │  Raw log events  ──►  Log Insights queries  ──►  Dashboards          │
  └──────────────────────────────────────────────────────────────────────┘

  Async invocation failures ──► SQS Dead-Letter Queue  ──►  Alert

  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
  │  EC2AutomationFn │  │  S3AutomationFn  │  │  SQSAutomationFn │
  │  boto3_ec2.py    │  │  boto3_s3.py     │  │  boto3_sqs.py    │
  │  list/start/stop │  │  list/presign/cp │  │  send/stats/peek │
  └──────────────────┘  └──────────────────┘  └──────────────────┘

  Local CLI:
  python src/boto3_lambda_manager.py --function BuggyLambda --scenario timeout --logs
```

---

## Key Concepts

| Concept | What it means |
|---------|--------------|
| **CloudWatch Log Groups** | One log group per Lambda function: `/aws/lambda/<FunctionName>` |
| **Log Streams** | One stream per container instance; scale-out creates multiple streams |
| **Log Insights** | SQL-like query language across log groups; great for searching errors |
| **Dead-Letter Queue** | Captures async invocation failures after Lambda's retry exhaustion |
| **Function Error vs HTTP Error** | Lambda returns HTTP 200 even if your code threw — check `FunctionError` |
| **Throttles** | Lambda's concurrency limit reached; messages retry automatically |
| **Init Duration** | Cold start cost — visible only in first REPORT line per container |

---

## Project Structure

```
lambda-troubleshooting-monitoring/
├── README.md
├── steps/
│   ├── 01-iam-role.md              ← Role with EC2, S3, SQS, CloudWatch permissions
│   ├── 02-setup-buggy-function.md  ← Deploy BuggyLambda
│   ├── 03-cloudwatch-logs.md       ← Navigate and read CloudWatch Logs
│   ├── 04-log-insights.md          ← Query logs with Log Insights
│   ├── 05-dead-letter-queue.md     ← Configure DLQ for async failures
│   ├── 06-boto3-ec2.md             ← Deploy and use EC2AutomationFn
│   ├── 07-boto3-s3.md              ← Deploy and use S3AutomationFn
│   ├── 08-boto3-sqs.md             ← Deploy and use SQSAutomationFn
│   └── 09-cleanup.md
├── src/
│   ├── buggy_functions.py          ← Multi-scenario broken handler
│   ├── boto3_ec2.py                ← Lambda: EC2 automation
│   ├── boto3_s3.py                 ← Lambda: S3 automation
│   ├── boto3_sqs.py                ← Lambda: SQS automation
│   └── boto3_lambda_manager.py     ← Local CLI tool: invoke, logs, insights, metrics
├── troubleshooting.md              ← The main troubleshooting reference
└── challenges.md
```

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| AWS account | Lambda, EC2, S3, SQS, IAM, CloudWatch, CloudWatch Log Insights |
| AWS CLI | v2.x |
| Python | 3.9+ locally |
| Boto3 | `pip install boto3` |
| Completed | [Lambda Basics](../lambda-basics/README.md), [Lambda Layers](../lambda-layers/README.md) (recommended) |

---

## Boto3 Scenarios Covered

| Handler | AWS Service | Operations |
|---------|-------------|------------|
| `buggy_functions.py` | Lambda | Unhandled errors, timeouts, OOM, env var errors |
| `boto3_ec2.py` | EC2 | List instances, start, stop, tag |
| `boto3_s3.py` | S3 | List buckets/objects, pre-signed URLs, copy |
| `boto3_sqs.py` | SQS | Send, stats, peek, purge |
| `boto3_lambda_manager.py` | Lambda + CloudWatch + Log Insights | Local management CLI |

---

## Step by Step

| Step | File | Goal |
|------|------|------|
| 1 | `01-iam-role.md` | Create a broad troubleshooting role (scoped to these resources) |
| 2 | `02-setup-buggy-function.md` | Deploy BuggyLambda and trigger each failure scenario |
| 3 | `03-cloudwatch-logs.md` | Read and filter raw CloudWatch log streams |
| 4 | `04-log-insights.md` | Query across invocations with Log Insights |
| 5 | `05-dead-letter-queue.md` | Capture async failures in a DLQ |
| 6 | `06-boto3-ec2.md` | Deploy and invoke the EC2 automation function |
| 7 | `07-boto3-s3.md` | Deploy and invoke the S3 automation function |
| 8 | `08-boto3-sqs.md` | Deploy and invoke the SQS automation function |
| 9 | `09-cleanup.md` | Remove all resources |

Start with **Step 1 →** [`steps/01-iam-role.md`](steps/01-iam-role.md)

---

## Estimated Time

3 – 4 hours (all steps). Steps 2–5 alone (troubleshooting focus): ~90 minutes.

## Estimated Cost

Within Free Tier for testing volumes. EC2 start/stop operations are free; only running EC2 instances incur cost. No EC2 instances are created in this project — only existing instances are queried.
