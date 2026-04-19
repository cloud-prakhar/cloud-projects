# Step 5 — Event Source Mapping: Connect SQS to Lambda

The **event source mapping** tells Lambda to poll `OrderQueue` and invoke `OrderProcessor` automatically whenever messages arrive. You do not write any polling code — AWS manages it.

---

## 5.1 Add the Trigger

1. Open the `OrderProcessor` Lambda function.
2. Click **+ Add trigger** (on the Function overview diagram).

| Field | Value |
|-------|-------|
| Trigger configuration | **SQS** |
| SQS queue | `OrderQueue` |
| Batch size | `5` |
| Batch window | `0` seconds |
| Report batch item failures | **Enabled** |

> **Batch size = 5:** Lambda receives up to 5 messages in a single invocation. For this project, 1–5 is fine.
>
> **Report batch item failures:** Must be enabled so Lambda's `batchItemFailures` response is respected. Without it, a single failed message causes the entire batch to be retried.

Click **Add**.

---

## 5.2 Verify the Trigger Appears

After a few seconds you should see **SQS** listed as a trigger in the Function overview. The state should be **Enabled**.

---

## How It Works Internally

```
SQS polls internally (AWS-managed)
    │
    │  up to 5 messages at a time
    ▼
Lambda invocation
    │
    ├── success  → SQS deletes those messages automatically
    └── failure  → those messageIds returned in batchItemFailures
                       └── SQS retries them (up to maxReceiveCount=3)
                                └── then moves to OrderDLQ
```

Lambda's event source mapping handles all of this. You only write the handler logic.

---

## 5.3 IAM Check

The `AWSLambdaSQSQueueExecutionRole` policy attached in Step 1 already grants:
- `sqs:ReceiveMessage`
- `sqs:DeleteMessage`
- `sqs:GetQueueAttributes`

No additional SQS resource policy is needed for the Lambda trigger.

---

**Next:** [Step 6 — Testing](./06-testing.md)
