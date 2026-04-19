# Step 2 — Create the SNS Topic

## What Is SNS?

Amazon SNS (Simple Notification Service) is a **pub/sub** (publish/subscribe) messaging service. Publishers send messages to a **Topic**, and SNS delivers that message to all subscribers. Subscribers can be SQS queues, Lambda functions, HTTP endpoints, email addresses, and more.

In this project, the SNS topic acts as the central hub that receives order events and fans them out to multiple queues.

---

## Step 2.1 — Open the SNS Console

1. Sign in to the AWS Console as `messaging-lab-user` (or your admin user)
2. In the search bar at the top, type **SNS** and click **Simple Notification Service**
3. Make sure you are in a region close to you (e.g., `us-east-1`). Note the region — you will use the same region for all resources in this project.

---

## Step 2.2 — Create the Topic

1. In the left sidebar, click **Topics** → **Create topic**
2. **Type:** Select **Standard**

   > **Standard vs FIFO:** Standard topics offer high throughput and at-least-once delivery but do not guarantee ordering. FIFO topics guarantee ordering and exactly-once delivery. For this lab, Standard is sufficient.

3. **Name:** `OrderEvents`
4. Leave all other settings at their defaults
5. Scroll down and click **Create topic**

---

## Step 2.3 — Note the Topic ARN

After creation, you will see the topic details page. Copy and save the **Topic ARN** — it looks like this:

```
arn:aws:sns:us-east-1:123456789012:OrderEvents
```

You will need this ARN in Step 4 when creating subscriptions.

---

## Verification

- Navigate to **Topics** in the left sidebar
- Confirm `OrderEvents` appears in the list with **Type: Standard**

---

## Key Concepts

| Concept | Explanation |
|---------|-------------|
| **SNS Topic** | A named channel that messages are published to |
| **Publisher** | Any entity (user, app, AWS service) that sends a message to a topic |
| **Subscriber** | Any endpoint (SQS, Lambda, email, etc.) that receives messages from a topic |
| **ARN** | Amazon Resource Name — a unique identifier for every AWS resource |
| **Standard Topic** | High-throughput, at-least-once delivery, no ordering guarantee |
| **FIFO Topic** | Ordered, exactly-once delivery, lower throughput |

---

Next: [Step 3 — Create the SQS Queues](./03-sqs-queues.md)
