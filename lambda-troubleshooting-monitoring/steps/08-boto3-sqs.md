# Step 8 — SQS Automation with Lambda and Boto3

Deploy the SQS automation function and test it against a live queue.

---

## 8.1 Create a Test SQS Queue

1. Open **SQS** in the AWS Console → **Create queue**.

   | Field | Value |
   |-------|-------|
   | Type | Standard |
   | Name | `LambdaTestQueue` |
   | Visibility timeout | 30 seconds |

2. Click **Create queue**. Copy the **URL** shown at the top.

---

## 8.2 Package and Create the Function

```bash
zip -j sqs_automation.zip src/boto3_sqs.py
```

1. **Lambda → Create function → Author from scratch**

   | Field | Value |
   |-------|-------|
   | Function name | `SQSAutomationFn` |
   | Runtime | **Python 3.14** |
   | Execution role | `LambdaTroubleshootingRole` |

2. Upload `sqs_automation.zip` → Handler: `boto3_sqs.handler` → Timeout: 30 sec.

---

## 8.3 Test: Send a Message

1. **Test** tab → Event name: `SendMessage`
2. Paste:
   ```json
   {
     "action": "send",
     "queue_name": "LambdaTestQueue",
     "message": "Hello from Lambda via Boto3!",
     "attributes": {"source": "Lambda", "project": "troubleshooting"}
   }
   ```
3. Click **Test**.

Expected response: `{ "message_id": "...", "queue": "LambdaTestQueue" }`

---

## 8.4 Test: Queue Statistics

1. Event name: `QueueStats`
2. Paste:
   ```json
   { "action": "stats", "queue_name": "LambdaTestQueue" }
   ```
3. Click **Test**.

The response shows:

| Field | What it means |
|-------|---------------|
| `messages_available` | Messages ready to be received |
| `messages_in_flight` | Received but not yet deleted (within visibility timeout) |
| `visibility_timeout_s` | How long received messages stay invisible to other consumers |
| `has_dlq` | Whether a Dead-Letter Queue is configured |

---

## 8.5 Test: Peek at Messages

1. Event name: `PeekMessages`
2. Paste:
   ```json
   { "action": "peek", "queue_name": "LambdaTestQueue", "max_messages": 3 }
   ```
3. Click **Test**.

> **Important:** `receive_message` makes the messages **invisible** for the Visibility Timeout (30 seconds). After 30 seconds they reappear. The `peek` action does NOT delete messages — it reads and releases them.

---

## 8.6 Test: Check the Dead-Letter Queue

After completing Step 5 (DLQ), you can check it here:

1. Event name: `DLQStats`
2. Paste:
   ```json
   { "action": "stats", "queue_name": "BuggyLambdaDLQ" }
   ```

If `messages_available > 0`, the async failure from Step 5 landed in the DLQ.

---

## 8.7 Run the Local Management Script

This script runs from your laptop using your local AWS credentials (not inside Lambda):

```bash
cd /path/to/lambda-troubleshooting-monitoring
pip install boto3

# Invoke a scenario and immediately fetch logs
python src/boto3_lambda_manager.py \
  --function BuggyLambda \
  --scenario unhandled_error \
  --logs

# Run a Log Insights query
python src/boto3_lambda_manager.py \
  --function BuggyLambda \
  --insights "filter @type = 'REPORT' | stats avg(@duration), count(*)"

# Show CloudWatch metrics
python src/boto3_lambda_manager.py \
  --function BuggyLambda \
  --metrics
```

---

## Checkpoint

- [ ] `SQSAutomationFn` deployed and Active
- [ ] `LambdaTestQueue` created
- [ ] Sent a message and verified it appeared in queue stats
- [ ] Peeked at messages and understood visibility timeout
- [ ] Ran `boto3_lambda_manager.py` locally with at least one flag

---

**Next:** [Step 9 — Cleanup](./09-cleanup.md)
