# Step 3 — Create the SQS Queues

## What Is SQS?

Amazon SQS (Simple Queue Service) is a fully managed **message queue**. Producers send messages into the queue, and consumers poll the queue to retrieve and process them. Unlike SNS, SQS stores messages durably — if a consumer is offline, the message waits in the queue until it is retrieved.

In this project, you will create two queues that both subscribe to the same SNS topic, demonstrating the **fanout** pattern.

---

## Step 3.1 — Open the SQS Console

1. In the AWS Console search bar, type **SQS** and click **Simple Queue Service**
2. Confirm you are in the **same region** you used in Step 2

---

## Step 3.2 — Create the Inventory Queue

1. Click **Create queue**
2. **Type:** Standard
3. **Name:** `InventoryQueue`
4. Under **Configuration**, leave defaults:
   - Visibility timeout: 30 seconds
   - Message retention period: 4 days
   - Delivery delay: 0 seconds
5. Leave **Access policy** set to **Basic** for now (you will update this in Step 4)
6. Click **Create queue**
7. Copy and save the **Queue URL** and **Queue ARN** from the details page

   Example ARN:
   ```
   arn:aws:sqs:us-east-1:123456789012:InventoryQueue
   ```

---

## Step 3.3 — Create the Notification Queue

1. Click **Create queue** again
2. **Type:** Standard
3. **Name:** `NotificationQueue`
4. Leave all other settings at defaults
5. Click **Create queue**
6. Copy and save the **Queue URL** and **Queue ARN**

---

## Verification

- In the SQS console, confirm both queues appear:
  - `InventoryQueue`
  - `NotificationQueue`
- Both should show **Type: Standard** and **Messages Available: 0**

---

## Understanding Key SQS Settings

| Setting | Default | Meaning |
|---------|---------|---------|
| **Visibility Timeout** | 30s | When a consumer receives a message, it is hidden from other consumers for this duration. If not deleted within this window, it becomes visible again. |
| **Message Retention Period** | 4 days | How long SQS keeps a message if it is not consumed. Max is 14 days. |
| **Delivery Delay** | 0s | Optional delay before a message becomes visible in the queue after being sent. |
| **Max Message Size** | 256 KB | Maximum size of a single message body. |

---

## Key Concepts

| Concept | Explanation |
|---------|-------------|
| **Queue** | A buffer that stores messages until a consumer retrieves them |
| **Producer** | Sends messages into the queue (in this project, SNS is the producer) |
| **Consumer** | Polls the queue and processes messages |
| **At-least-once delivery** | SQS Standard may deliver a message more than once — consumers should handle duplicates (idempotency) |
| **Standard Queue** | High throughput, at-least-once delivery, best-effort ordering |

---

Next: [Step 4 — Subscribe Queues to the SNS Topic](./04-sns-sqs-subscription.md)
