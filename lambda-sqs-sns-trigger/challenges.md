# Challenges

Extend the project after completing the core steps.

---

## Challenge 1 — Filter SNS Subscriptions by Order Value

SNS supports **subscription filter policies** so each subscriber only receives messages matching certain attributes.

**Goal:** Add a second email subscription that receives only orders where `amount > 100`.

**Hints:**
- In the Lambda code, `MessageAttributes` already includes `eventType`. Add an `orderTier` attribute: `"HIGH_VALUE"` if amount > 100, else `"STANDARD"`.
- In SNS → Subscription → Edit → Subscription filter policy, filter on `orderTier = HIGH_VALUE`.

---

## Challenge 2 — Add a FIFO Queue for Strict Ordering

The current `OrderQueue` is a Standard queue (at-least-once, best-effort ordering). FIFO queues guarantee exactly-once processing and strict ordering.

**Goal:** Create `OrderQueue.fifo` (FIFO), update the event source mapping, and send messages with a `MessageGroupId`.

**Hints:**
- FIFO queue names must end in `.fifo`
- `send-message` requires `--message-group-id` and `--message-deduplication-id`
- Lambda + FIFO: one concurrent execution per message group

---

## Challenge 3 — Dead-Letter Queue Alarm

**Goal:** Create a CloudWatch Alarm that emails you when `OrderDLQ` has more than 0 messages (meaning Lambda is failing to process orders).

**Hints:**
- CloudWatch → Alarms → Create alarm
- Metric: `SQS → ApproximateNumberOfMessagesVisible` for `OrderDLQ`
- Threshold: `> 0` for 1 evaluation period
- Action: send to an SNS topic with your email subscribed

---

## Challenge 4 — Idempotent Processing

SQS Standard queues guarantee **at-least-once** delivery — the same message can be delivered more than once. Duplicate SNS notifications would be a poor customer experience.

**Goal:** Make `OrderProcessor` idempotent using DynamoDB.

**Hints:**
- Before publishing to SNS, check a DynamoDB table for the `orderId`
- If it exists, skip the publish and return success
- If it doesn't exist, publish to SNS and write the `orderId` to DynamoDB (with a TTL of 24 hours)
- Add `AmazonDynamoDBFullAccess` (or a scoped custom policy) to the execution role

---

## Challenge 5 — Deploy with AWS SAM

Instead of clicking through the console, define the entire stack as Infrastructure as Code.

**Goal:** Write a `template.yaml` using AWS SAM that defines:
- `OrderQueue` (SQS) with a DLQ
- `OrderNotifications` (SNS topic)
- `OrderProcessor` (Lambda) with the SQS event source mapping and `SNS_TOPIC_ARN` env var wired automatically

**Hints:**
- `sam init` bootstraps a project
- `AWS::Serverless::Function` supports `Events.SQSTrigger` of type `SQS`
- Use `!GetAtt OrderNotifications.Arn` to pass the topic ARN as an environment variable without hardcoding it

---

## Challenge 6 — Structured Logging and X-Ray Tracing

**Goal:** Add structured JSON logging and enable AWS X-Ray so you can trace a request from SQS receipt through Lambda to SNS.

**Hints:**
- Use `aws_lambda_powertools` (`Logger`, `Tracer`) — installable via a Lambda Layer
- Enable **Active tracing** on the Lambda function (Configuration → Monitoring and operations tools)
- Add `AWSXRayDaemonWriteAccess` to the execution role
