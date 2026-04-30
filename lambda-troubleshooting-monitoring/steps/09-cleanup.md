# Step 9 — Cleanup

Remove all resources created in this project.

---

## Resources to Delete

| Resource | Name |
|----------|------|
| Lambda function | `BuggyLambda` |
| Lambda function | `EC2AutomationFn` |
| Lambda function | `S3AutomationFn` |
| Lambda function | `SQSAutomationFn` |
| SQS queue | `BuggyLambdaDLQ` |
| SQS queue | `LambdaTestQueue` |
| CloudWatch Alarm | `BuggyLambdaDLQ-NotEmpty` (if created) |
| EventBridge rule | `StopDevInstancesEvening` (if created) |
| IAM inline policies | `EC2AutomationPolicy`, `S3AutomationPolicy`, `SQSAutomationPolicy`, `DLQWritePolicy` |
| IAM managed policy | `AWSLambdaBasicExecutionRole` (attached to role) |
| IAM role | `LambdaTroubleshootingRole` |
| CloudWatch log groups | `/aws/lambda/BuggyLambda`, `/aws/lambda/EC2AutomationFn`, etc. |

---

## Cleanup Script

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. Delete Lambda functions
for FN in BuggyLambda EC2AutomationFn S3AutomationFn SQSAutomationFn; do
  aws lambda delete-function --function-name "$FN" 2>/dev/null && echo "✓ Deleted Lambda: $FN"
done

# 2. Delete SQS queues
for QUEUE in BuggyLambdaDLQ LambdaTestQueue; do
  URL=$(aws sqs get-queue-url --queue-name "$QUEUE" --query QueueUrl --output text 2>/dev/null)
  if [ -n "$URL" ]; then
    aws sqs delete-queue --queue-url "$URL"
    echo "✓ Deleted SQS queue: $QUEUE"
  fi
done

# 3. Delete CloudWatch alarm (if created)
aws cloudwatch delete-alarms --alarm-names BuggyLambdaDLQ-NotEmpty 2>/dev/null && echo "✓ Alarm deleted"

# 4. Delete EventBridge rule (if created)
aws events remove-targets --rule StopDevInstancesEvening --ids StopDevInstances 2>/dev/null
aws events delete-rule --name StopDevInstancesEvening 2>/dev/null && echo "✓ EventBridge rule deleted"

# 5. Delete CloudWatch log groups
for FN in BuggyLambda EC2AutomationFn S3AutomationFn SQSAutomationFn; do
  aws logs delete-log-group \
    --log-group-name "/aws/lambda/${FN}" 2>/dev/null && echo "✓ Log group deleted: /aws/lambda/$FN"
done

# 6. Detach managed policy
aws iam detach-role-policy \
  --role-name LambdaTroubleshootingRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>/dev/null

# 7. Delete inline policies
for POLICY in EC2AutomationPolicy S3AutomationPolicy SQSAutomationPolicy DLQWritePolicy; do
  aws iam delete-role-policy \
    --role-name LambdaTroubleshootingRole \
    --policy-name "$POLICY" 2>/dev/null && echo "✓ Inline policy deleted: $POLICY"
done

# 8. Delete IAM role
aws iam delete-role --role-name LambdaTroubleshootingRole 2>/dev/null && echo "✓ IAM role deleted"

# 9. Local cleanup
rm -f *.zip /tmp/ec2_response.json /tmp/s3_response.json /tmp/sqs_response.json /tmp/response.json
echo "✓ Local files cleaned"

echo ""
echo "All resources deleted."
```

---

## Verification

```bash
# All of these should return errors (not found)
aws lambda list-functions \
  --query "Functions[?contains(FunctionName, 'BuggyLambda') || contains(FunctionName, 'AutomationFn')].FunctionName"

aws sqs list-queues \
  --queue-name-prefix BuggyLambdaDLQ

aws iam get-role --role-name LambdaTroubleshootingRole 2>&1 | grep -i "not found\|cannot be found"
```

---

## Well done — Series Complete!

You have completed all four Lambda projects:

| Project | Skills Learned |
|---------|---------------|
| [Lambda Basics](../../lambda-basics/README.md) | Handler, context, CloudWatch Logs, env vars |
| [Lambda + S3](../../lambda-s3-event-processing/README.md) | Event-driven triggers, S3 integration, URL decoding |
| [Lambda Layers](../../lambda-layers/README.md) | Dependency packaging, native extensions, layer versioning |
| [Troubleshooting + Boto3](../../lambda-troubleshooting-monitoring/README.md) | CloudWatch Logs, Log Insights, DLQs, EC2/S3/SQS automation |
