# Lambda Triggered by SQS with SNS Notification

## What You'll Build

You will build an **order processing pipeline** — a classic serverless pattern where:

1. A producer sends an order message to an **SQS queue**
2. **Lambda** is automatically triggered by the SQS event source mapping
3. Lambda processes the order and publishes a result notification to an **SNS topic**
4. SNS fans the notification out to subscribers (email, another SQS queue, etc.)

This mirrors real-world order-processing, payment workflows, and async job pipelines.

---

## Architecture

```
                    ┌──────────────────────┐
                    │     Producer         │
                    │ (you, via CLI/SDK)   │
                    └──────────┬───────────┘
                               │ SendMessage
                               ▼
                    ┌──────────────────────┐
                    │     SQS Queue        │
                    │   "OrderQueue"       │
                    │  (+ Dead-Letter Q)   │
                    └──────────┬───────────┘
                               │ Event Source Mapping
                               │ (Lambda polls SQS)
                               ▼
                    ┌──────────────────────┐
                    │   Lambda Function    │
                    │  "OrderProcessor"    │
                    │  (Python 3.14)       │
                    └────┬─────────────────┘
                         │
          ┌──────────────┴──────────────────────┐
          │ on success                           │ on success + failure
          ▼                                      ▼
┌─────────────────────┐             ┌──────────────────────┐
│     SNS Topic       │             │     SNS Topic        │
│ "OrderNotifications"│             │    "OrderAlerts"     │
│  (business events)  │             │  (ops visibility)    │
└────────┬────────────┘             └──────────┬───────────┘
    ┌────┴────┐                                 │
    ▼         ▼                      email (status=SUCCESS or FAILED)
 Email      SQS                      optional filter: status=FAILED only
 inbox   "ProcessedOrders"
```

**Key concepts:**
- **SQS → Lambda trigger:** Lambda's event source mapping polls SQS. You don't manage polling — AWS does.
- **Dead-Letter Queue (DLQ):** Messages that fail repeatedly land in the DLQ instead of being lost.
- **Partial batch failure:** Lambda reports failed message IDs; SQS retries only those, not the whole batch.
- **Two SNS topics:** `OrderNotifications` carries business events for downstream services (success only). `OrderAlerts` carries operational signals — success and failure — for operators and monitoring, with a `status` message attribute so subscribers can filter by outcome.

---

## AWS Services Used

| Service | Role |
|---------|------|
| **SQS** | Durable inbound queue; buffers order messages; triggers Lambda |
| **Lambda** | Serverless compute; processes each order; publishes result to SNS |
| **SNS** | Notification broker; fans processed-order events out to subscribers |
| **IAM** | Execution role granting Lambda permission to read SQS and write to SNS |

---

## What You'll Learn

- How to create an SQS Standard queue and a Dead-Letter Queue
- How to create a Lambda function with a Python runtime
- How to attach an IAM execution role with least-privilege permissions
- How to wire an SQS event source mapping to a Lambda function
- How to publish messages to SNS from inside a Lambda function
- How partial batch failure responses improve retry behavior
- How to subscribe email and SQS endpoints to an SNS topic
- How to test the end-to-end pipeline and read logs in CloudWatch
- How to clean up all resources to avoid charges

---

## Lambda Code

The Lambda handler lives at [`lambda/handler.py`](./lambda/handler.py).

Key behaviors:
- Iterates over `event["Records"]` (SQS batch)
- Parses each message body as JSON
- On success: publishes processed order to `OrderNotifications`; publishes a `SUCCESS` alert to `OrderAlerts`
- On failure: publishes a `FAILED` alert to `OrderAlerts` with the error and raw SQS body; returns the message ID in `batchItemFailures` so SQS retries only that record
- `ALERT_SNS_TOPIC_ARN` is optional — alerts are silently skipped if the env var is not set

---

## Steps

Follow these in order:

1. [IAM — Create the Lambda execution role](./steps/01-iam-role.md)
2. [SQS — Create OrderQueue and Dead-Letter Queue](./steps/02-sqs-queues.md)
3. [SNS — Create OrderNotifications topic and subscribe](./steps/03-sns-topic.md)
4. [Lambda — Create and deploy the function](./steps/04-lambda-function.md)
5. [Event Source Mapping — Connect SQS to Lambda](./steps/05-event-source-mapping.md)
6. [Testing — Send a message and verify the pipeline](./steps/06-testing.md)
7. [Cleanup — Delete all resources](./steps/07-cleanup.md)

---

## Troubleshooting

See [troubleshooting.md](./troubleshooting.md) for common errors and fixes.

## Challenges

See [challenges.md](./challenges.md) to extend the project after completing the core steps.

---

## Estimated AWS Cost

All resources fall within the **AWS Free Tier**:
- Lambda: First 1 million requests/month free
- SQS: First 1 million requests/month free
- SNS: First 1 million publishes/month free; first 1,000 email notifications/month free
- CloudWatch Logs: First 5 GB ingestion/month free

> Always run [Step 7 — Cleanup](./steps/07-cleanup.md) when you are done.
