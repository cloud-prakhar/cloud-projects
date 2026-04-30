# Step 3 — Reading CloudWatch Logs for Lambda Troubleshooting

CloudWatch Logs is the primary observability tool for Lambda. This step teaches you to navigate log groups, interpret the standard Lambda log format, and find specific errors.

---

## 3.1 Open the Log Group in the Console

1. Open **Lambda → BuggyLambda → Monitor** tab.
2. Click **View CloudWatch logs** — this opens `/aws/lambda/BuggyLambda` directly.

Alternatively:

1. Open **CloudWatch → Log groups**.
2. Search for `/aws/lambda/BuggyLambda` and click it.

---

## 3.2 Understand Log Streams

Each Lambda **container instance** writes to its own **log stream**. You'll see one or more streams named like:

```
2026/04/30/[$LATEST]f1b076933ffe4bb8a1688b650b77a4d3
```

- The date prefix shows when the container was created
- `$LATEST` means the most recent unpublished version
- The random suffix identifies the specific container

Click the most recent stream to see your invocations.

---

## 3.3 Read a Log Entry

Every Lambda invocation produces this structure:

```
START RequestId: abc123  Version: $LATEST
INFO    Running scenario: unhandled_error | request_id: abc123
[ERROR] ValueError: Something went wrong — this is intentional for learning.
Traceback (most recent call last):
  File "/var/task/buggy_functions.py", line 52, in handler
    return fn(event, context)
  ...
END RequestId: abc123
REPORT RequestId: abc123  Duration: 1.23 ms  Billed Duration: 2 ms  Memory Size: 128 MB  Max Memory Used: 37 MB
```

| Line | What it means |
|------|---------------|
| `START` | Invocation begins; note the `RequestId` for this invocation |
| `INFO` | Lines from `logger.info()` or `print()` in your code |
| `[ERROR]` | Unhandled exception — Lambda prepends this tag automatically |
| `END` | Invocation finished (or was killed) |
| `REPORT` | Billing and performance summary |

---

## 3.4 Find a Cold Start

Look for `Init Duration` in a REPORT line:

```
REPORT RequestId: ...  Duration: 412 ms  ...  Init Duration: 950.51 ms
```

`Init Duration` only appears on a **cold start** — the first invocation after the container is created. Subsequent warm invocations will not have it. You'll notice the total billed duration equals `Duration + Init Duration` on cold starts.

---

## 3.5 Filter Log Events in the Console

1. On the log group page, click **Search all log streams**.
2. In the filter bar, type `[ERROR]` and press Enter.
3. The view now shows only error lines across all streams.

Useful filter patterns:

| Pattern | Matches |
|---------|---------|
| `[ERROR]` | Unhandled exceptions |
| `Task timed out` | Timeout events |
| `Init Duration` | Cold starts (in REPORT lines) |
| `signal: killed` | Out-of-memory container kills |

---

## 3.6 Find a Specific Invocation by Request ID

When a user reports an error and gives you a Request ID:

1. On the log group page, click **Search all log streams**.
2. Type the Request ID (e.g., `abc-123-your-request-id`) in the filter.
3. All log lines for that specific invocation appear.

---

## 3.7 Use the CLI to Filter Errors

```bash
# Show only [ERROR] lines from the last 30 minutes
aws logs filter-log-events \
  --log-group-name /aws/lambda/BuggyLambda \
  --start-time $(($(date +%s%3N) - 1800000)) \
  --filter-pattern "[ERROR]" \
  --query 'events[*].message' \
  --output text

# Find all timeout events
aws logs filter-log-events \
  --log-group-name /aws/lambda/BuggyLambda \
  --start-time $(($(date +%s%3N) - 1800000)) \
  --filter-pattern '"Task timed out"' \
  --query 'events[*].message' \
  --output text

# Tail logs in real time (AWS CLI v2)
aws logs tail /aws/lambda/BuggyLambda --follow
```

---

## Checkpoint

- [ ] Navigated to `/aws/lambda/BuggyLambda` in CloudWatch
- [ ] Identified START, INFO, [ERROR], END, and REPORT lines
- [ ] Used the Console filter to show only `[ERROR]` lines
- [ ] Found at least one cold start (Init Duration in REPORT line)
- [ ] Located all error scenarios from Step 2 in the logs

---

**Next:** [Step 4 — CloudWatch Log Insights](./04-log-insights.md)
