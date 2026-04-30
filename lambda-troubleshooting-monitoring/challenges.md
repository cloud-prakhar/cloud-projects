# Challenges — Lambda Troubleshooting & Monitoring

---

## Challenge 1 — Structured JSON Logging

Modify `buggy_functions.py` to log in JSON format for every handler call:

```json
{"timestamp": "2026-04-30T12:00:00Z", "level": "INFO", "request_id": "abc123", "scenario": "ok", "message": "Running scenario"}
```

Then in CloudWatch Log Insights, use the `parse` command to extract JSON fields:

```sql
fields @message
| filter ispresent(scenario)
| stats count(*) by scenario
```

JSON-structured logs let Log Insights query individual fields directly, making cross-invocation analysis much more powerful.

---

## Challenge 2 — Custom CloudWatch Metric

Emit a custom CloudWatch metric from `boto3_sqs.py` every time a message is sent:

```python
cloudwatch = boto3.client("cloudwatch")
cloudwatch.put_metric_data(
    Namespace="LambdaProject4",
    MetricData=[{
        "MetricName": "MessagesSent",
        "Value": 1,
        "Unit": "Count",
        "Dimensions": [{"Name": "QueueName", "Value": queue_name}],
    }]
)
```

Then create a CloudWatch dashboard widget showing this metric alongside the built-in Lambda `Invocations` metric.

---

## Challenge 3 — CloudWatch Alarm on Error Rate

Create a CloudWatch Alarm that triggers when `BuggyLambda`'s error rate exceeds 20% over a 5-minute window:

1. Create an SNS topic and subscribe your email
2. Create an alarm on the `Errors` metric for `BuggyLambda`
3. Trigger 5 `unhandled_error` invocations in quick succession
4. Verify you receive the alarm email

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name BuggyLambdaHighErrorRate \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --dimensions "Name=FunctionName,Value=BuggyLambda" \
  --statistic Sum \
  --period 300 \
  --threshold 3 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:us-east-1:<ACCOUNT_ID>:YourAlertTopic"
```

---

## Challenge 4 — Automated DLQ Processor

Write a new Lambda function (`DLQProcessor`) that:

1. Is triggered on a schedule (every 5 minutes via EventBridge)
2. Reads up to 10 messages from `BuggyLambdaDLQ` using `receive_message`
3. Logs each message's body and original RequestId
4. Deletes each message after logging (simulating "processed")
5. If no messages, logs "DLQ is empty — nothing to process"

This simulates real-world DLQ drain pipelines used to replay or archive failed events.

---

## Challenge 5 — Lambda as a Cron Job

Use EventBridge to invoke `SQSAutomationFn` every minute to report the depth of `LambdaTestQueue` and compare it against a threshold. If the depth exceeds 10 messages, have the function send an alert message to a separate `AlertQueue`.

This simulates a queue-depth monitoring pattern used in production to catch runaway producers before downstream services are overwhelmed.
