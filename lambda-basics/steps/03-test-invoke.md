# Step 3 — Test, Invoke, and Read CloudWatch Logs

In this step you invoke `HelloWorldLambda` multiple ways, then trace each invocation through CloudWatch Logs.

---

## Method 1 — AWS Console Test

### 1. Create a test event

On the Lambda function page, click the **Test** tab.

Click **Create new event**:

| Field | Value |
|-------|-------|
| Event name | `TestAlice` |
| Template | `hello-world` (or clear the JSON and paste below) |

Paste this JSON:

```json
{
  "name": "Alice"
}
```

Click **Save**, then **Test**.

### 2. Read the result

In the **Execution result** panel you see:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Hello, Alice! This is your first Lambda function.\"}"
}
```

Expand the **Log output** section — you'll see everything your logger wrote:

```
START RequestId: abc123 Version: $LATEST
INFO Event received: {"name": "Alice"}
INFO Function name      : HelloWorldLambda
INFO Function version   : $LATEST
INFO Invocation ID      : abc123
INFO Memory limit (MB)  : 128
INFO Remaining time (ms): 9987
END RequestId: abc123
REPORT RequestId: abc123  Duration: 2.41 ms  Billed Duration: 3 ms  Memory Size: 128 MB  Max Memory Used: 36 MB
```

Key fields in the REPORT line:

| Field | Meaning |
|-------|---------|
| Duration | Actual wall-clock time your code ran |
| Billed Duration | Rounded up to next 1 ms (the unit AWS charges for) |
| Max Memory Used | Peak RSS during this invocation |
| Init Duration | Only appears on a **cold start** — time to initialise the container |

---

## Method 2 — AWS CLI

```bash
# Synchronous invocation — blocks until function returns
aws lambda invoke \
  --function-name HelloWorldLambda \
  --cli-binary-format raw-in-base64-out \
  --payload '{"name": "Bob"}' \
  response.json

cat response.json
```

Output:

```json
{
    "statusCode": 200,
    "body": "{\"message\": \"Hello, Bob! This is your first Lambda function.\"}"
}
```

The `aws lambda invoke` command also prints the HTTP status code of the *invocation itself* (200 = success, 200 even if your function throws — the function's own error is in the payload).

```bash
# Asynchronous invocation — fire and forget, returns immediately
aws lambda invoke \
  --function-name HelloWorldLambda \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload '{"name": "Async"}' \
  /dev/null
```

With `Event` invocation type you get HTTP 202 Accepted. The function runs in the background. You'll see its log in CloudWatch a few seconds later.

---

## Method 3 — Boto3 Python Script

```bash
pip install boto3
python src/test_invoke.py
```

This script (see `src/test_invoke.py`) iterates over three payloads and prints each response. Study how it uses `client.invoke()` and decodes `response["Payload"]`.

---

## Reading Logs in CloudWatch

### Via the Console

1. Navigate to **CloudWatch → Log groups**
2. Open `/aws/lambda/HelloWorldLambda`
3. Each invocation creates or appends to a **log stream** named with the date and a random suffix

> Log streams are per container instance. If Lambda scales to 3 concurrent instances you'll see 3 streams. This is normal.

### Via the CLI

```bash
# List log streams (most recent first)
aws logs describe-log-streams \
  --log-group-name /aws/lambda/HelloWorldLambda \
  --order-by LastEventTime \
  --descending \
  --query 'logStreams[0].logStreamName' \
  --output text

# Store the stream name
STREAM=$(aws logs describe-log-streams \
  --log-group-name /aws/lambda/HelloWorldLambda \
  --order-by LastEventTime \
  --descending \
  --query 'logStreams[0].logStreamName' \
  --output text)

# Fetch the last 20 log events
aws logs get-log-events \
  --log-group-name /aws/lambda/HelloWorldLambda \
  --log-stream-name "$STREAM" \
  --limit 20 \
  --query 'events[*].message' \
  --output text
```

### Via CloudWatch Log Insights (quick query)

1. Open **CloudWatch → Log Insights**
2. Select log group: `/aws/lambda/HelloWorldLambda`
3. Run:

```sql
fields @timestamp, @message
| filter @message like /Hello/
| sort @timestamp desc
| limit 20
```

This returns only the log lines containing "Hello" — useful when you have many invocations.

---

## Understanding Cold vs Warm Starts

Invoke the function twice in quick succession:

```bash
for i in 1 2; do
  aws lambda invoke \
    --function-name HelloWorldLambda \
    --cli-binary-format raw-in-base64-out \
    --payload "{\"name\": \"Run$i\"}" \
    /dev/null
  sleep 1
done
```

In CloudWatch, look for `Init Duration` in the REPORT line. You'll see it only on the first invocation (cold start). The second reuses the warm container.

---

## Checkpoint

- [ ] Invoked via Console test and saw the correct JSON response
- [ ] Invoked via CLI with a custom payload
- [ ] Ran `test_invoke.py` and saw output for all three payloads
- [ ] Found the log group `/aws/lambda/HelloWorldLambda` in CloudWatch
- [ ] Can explain the difference between Duration and Billed Duration

---

**Next →** [04-environment-variables.md](04-environment-variables.md)
