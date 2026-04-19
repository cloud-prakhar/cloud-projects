# Event-Driven Messaging with SNS & SQS

## What You'll Build

You will build an **order notification system** that uses the SNS fanout pattern — a common real-world architecture used by e-commerce platforms, logistics systems, and microservices.

When an order is placed, a single SNS message fans out to two independent SQS queues:
- An **Inventory Queue** (simulates updating stock levels)
- A **Notification Queue** (simulates sending a confirmation email)

Both queues receive the same message independently, and each can be processed by a different service.

---

## Architecture

```
                         ┌─────────────────────┐
                         │    Order Service     │
                         │  (you, via console)  │
                         └──────────┬──────────┘
                                    │ Publish message
                                    ▼
                         ┌─────────────────────┐
                         │     SNS Topic        │
                         │   "OrderEvents"      │
                         └────────┬────────────┘
                    SQS           │           SQS
                 Subscription     │        Subscription
               ┌─────────────────┴──────────────────┐
               ▼                                     ▼
  ┌────────────────────────┐         ┌────────────────────────┐
  │      SQS Queue         │         │      SQS Queue         │
  │   "InventoryQueue"     │         │  "NotificationQueue"   │
  └────────────────────────┘         └────────────────────────┘
```

**Key concept — Fanout:** One SNS publish → N SQS queues receive a copy. Queues are decoupled from each other and from the publisher.

---

## AWS Services Used

| Service | Role in This Project |
|---------|----------------------|
| **SNS** (Simple Notification Service) | Message broker / topic that fans out to subscribers |
| **SQS** (Simple Queue Service) | Durable queues that hold messages for downstream processing |
| **IAM** | Least-privilege user and resource policy to control who can publish and consume |

---

## What You'll Learn

- How to create an SNS Topic and publish messages to it
- How to create SQS Standard queues
- How to subscribe SQS queues to an SNS topic (fanout pattern)
- How to set SQS access policies so SNS can deliver messages
- How to create an IAM user with least-privilege permissions
- How to poll and receive messages from an SQS queue
- How to clean up AWS resources to avoid charges

---

## Steps

Follow these in order:

1. [IAM Setup — Create a least-privilege user](./steps/01-iam-setup.md)
2. [Create the SNS Topic](./steps/02-sns-topic.md)
3. [Create the SQS Queues](./steps/03-sqs-queues.md)
4. [Subscribe Queues to the SNS Topic](./steps/04-sns-sqs-subscription.md)
5. [Publish a message and verify fanout](./steps/05-testing.md)
6. [Cleanup — Delete all resources](./steps/06-cleanup.md)

---

## Troubleshooting

See [troubleshooting.md](./troubleshooting.md) for common errors and how to fix them.

## Challenges

See [challenges.md](./challenges.md) to go deeper after completing the core steps.

---

## Estimated AWS Cost

All resources used in this project fall within the **AWS Free Tier**:
- SNS: First 1 million publishes/month free
- SQS: First 1 million requests/month free
- IAM: Always free

> Always run [Step 6 — Cleanup](./steps/06-cleanup.md) when you are done to delete all resources.
