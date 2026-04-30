# Step 5 — Dead-Letter Queue for Async Lambda Failures

When Lambda is invoked **asynchronously** (Event invocation type, S3 triggers, SNS, etc.), it retries failed invocations up to 2 additional times by default. After all retries are exhausted, the event is either discarded silently or sent to a **Dead-Letter Queue (DLQ)** — a safety net you configure.

Without a DLQ, failed async events are **lost forever**. With a DLQ, you can inspect what failed, alert on it, and replay events after fixing the bug.

---

## Create the DLQ

```bash
aws sqs create-queue \
  --queue-name BuggyLambdaDLQ \
  --attributes VisibilityTimeout=60,MessageRetentionPeriod=1209600
```

`MessageRetentionPeriod=1209600` = 14 days (maximum). Failed events stay in the DLQ for up to 14 days for inspection.

Get the DLQ ARN:

```bash
DLQ_URL=$(aws sqs get-queue-url --queue-name BuggyLambdaDLQ --query QueueUrl --output text)
DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' --output text)

echo "DLQ ARN: $DLQ_ARN"
```

---

## Grant Lambda Permission to Write to the DLQ

The Lambda execution role needs `sqs:SendMessage` on the DLQ. Add it to the existing `SQSAutomationPolicy` or create a separate policy:

```bash
aws iam put-role-policy \
  --role-name LambdaTroubleshootingRole \
  --policy-name DLQWritePolicy \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{
      \"Effect\": \"Allow\",
      \"Action\": \"sqs:SendMessage\",
      \"Resource\": \"${DLQ_ARN}\"
    }]
  }"
```

---

## Configure the DLQ on BuggyLambda

```bash
aws lambda update-function-configuration \
  --function-name BuggyLambda \
  --dead-letter-config "TargetArn=${DLQ_ARN}"

aws lambda wait function-updated --function-name BuggyLambda
echo "DLQ configured"
```

---

## Configure Retry Behaviour (Optional)

By default Lambda retries async invocations 2 times (3 total attempts). You can change this:

```bash
aws lambda put-function-event-invoke-config \
  --function-name BuggyLambda \
  --maximum-retry-attempts 1 \
  --maximum-event-age-in-seconds 300
```

With `maximum-retry-attempts=1`: one retry (2 total attempts) before the event goes to the DLQ. With `maximum-event-age-in-seconds=300`: events older than 5 minutes are discarded without retrying.

---

## Trigger a DLQ Event

Invoke the function **asynchronously** with a failing scenario:

```bash
aws lambda invoke \
  --function-name BuggyLambda \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload '{"scenario": "unhandled_error"}' \
  /dev/null

echo "Async invocation sent (HTTP 202 = accepted)"
echo "Lambda will retry and then send the failed event to the DLQ."
echo "Wait ~2 minutes for retries to complete..."
```

---

## Inspect the DLQ

After ~2 minutes (time for Lambda's retries to complete):

```bash
aws sqs receive-message \
  --queue-url "$DLQ_URL" \
  --max-number-of-messages 1 \
  --wait-time-seconds 10 \
  --attribute-names All \
  --query 'Messages[0]'
```

The DLQ message contains:

| Attribute | Value |
|-----------|-------|
| `Body` | The original event payload (`{"scenario": "unhandled_error"}`) |
| `requestId` | The Lambda RequestId of the failed invocation |
| `condition` | `RetriesExhausted` — why it landed in the DLQ |
| `approximateReceiveCount` | How many times the message was received |

---

## Read the Original Failed Event

```bash
aws sqs receive-message \
  --queue-url "$DLQ_URL" \
  --max-number-of-messages 1 \
  --attribute-names All | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
msg = data['Messages'][0]
print('Original event:', msg['Body'])
print('Attributes:', json.dumps(msg['Attributes'], indent=2))
"
```

---

## Alert on DLQ Messages (Bonus)

In production, you'd want a CloudWatch Alarm that fires when the DLQ has messages:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name BuggyLambdaDLQ-NotEmpty \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --dimensions "Name=QueueName,Value=BuggyLambdaDLQ" \
  --statistic Maximum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:us-east-1:${ACCOUNT_ID}:YourAlertTopic" \
  --treat-missing-data notBreaching
```

---

## Checkpoint

- [ ] DLQ `BuggyLambdaDLQ` created
- [ ] DLQ ARN configured on `BuggyLambda`
- [ ] Sent an async invocation with a failing scenario
- [ ] After ~2 minutes, found the original event in the DLQ
- [ ] Can explain what "retries exhausted" means in this context

---

**Next →** [06-boto3-ec2.md](06-boto3-ec2.md)
