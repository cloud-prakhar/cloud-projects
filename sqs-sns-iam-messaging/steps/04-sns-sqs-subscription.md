# Step 4 — Subscribe SQS Queues to the SNS Topic

## Why This Step Is Critical

For SNS to deliver messages into an SQS queue, two things must be true:

1. **A subscription** must exist linking the SNS topic to the SQS queue
2. **The SQS queue's access policy** must allow SNS to send messages to it

If either is missing, messages will not arrive in the queue. This is one of the most common sources of confusion — you will learn both here.

---

## Step 4.1 — Subscribe InventoryQueue to OrderEvents

1. Go to the **SNS Console** → **Topics** → click `OrderEvents`
2. Scroll down to **Subscriptions** → click **Create subscription**
3. **Topic ARN:** already filled in as `OrderEvents`
4. **Protocol:** Select **Amazon SQS**
5. **Endpoint:** Paste the ARN of `InventoryQueue`
   ```
   arn:aws:sqs:us-east-1:123456789012:InventoryQueue
   ```
6. Leave **Enable raw message delivery** unchecked

   > **Raw message delivery:** When disabled (default), SNS wraps the message in a JSON envelope containing metadata (topic ARN, message ID, timestamp, etc.). When enabled, only the raw message body is delivered. Leave it off for now so you can see the full SNS envelope.

7. Click **Create subscription**
8. The subscription status should show **Confirmed** immediately (SQS subscriptions auto-confirm)

---

## Step 4.2 — Subscribe NotificationQueue to OrderEvents

Repeat the process:

1. In the `OrderEvents` topic, click **Create subscription** again
2. **Protocol:** Amazon SQS
3. **Endpoint:** Paste the ARN of `NotificationQueue`
4. Click **Create subscription**

---

## Step 4.3 — Update the SQS Access Policies

By default, SQS queues only allow the queue owner to send messages. You need to explicitly allow the SNS topic to send messages into each queue.

### For InventoryQueue:

1. Go to **SQS Console** → click `InventoryQueue`
2. Click the **Access policy** tab → **Edit**
3. Replace the existing policy with the following (substitute your own Account ID and region):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOwnerAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<YOUR_ACCOUNT_ID>:root"
      },
      "Action": "sqs:*",
      "Resource": "arn:aws:sqs:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:InventoryQueue"
    },
    {
      "Sid": "AllowSNSDelivery",
      "Effect": "Allow",
      "Principal": {
        "Service": "sns.amazonaws.com"
      },
      "Action": "sqs:SendMessage",
      "Resource": "arn:aws:sqs:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:InventoryQueue",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "arn:aws:sns:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:OrderEvents"
        }
      }
    }
  ]
}
```

4. Click **Save**

> **Condition explained:** The `ArnEquals` condition ensures only the `OrderEvents` topic can send messages — not any other SNS topic in your account. This is a security best practice.

### For NotificationQueue:

Repeat Step 4.3 for `NotificationQueue`, replacing `InventoryQueue` with `NotificationQueue` in all places.

---

## Verification

1. Go to **SNS Console** → **Topics** → `OrderEvents` → **Subscriptions** tab
2. Confirm you see **two subscriptions**, both with status **Confirmed**:
   - `InventoryQueue`
   - `NotificationQueue`

---

## Key Concepts

| Concept | Explanation |
|---------|-------------|
| **Subscription** | A link between an SNS topic and a specific endpoint (SQS, Lambda, email, etc.) |
| **Resource Policy** | A policy attached to an AWS resource (like an SQS queue) that controls who can access it |
| **Principal** | The identity being granted or denied access in a policy statement |
| **Condition key** | Extra constraints in a policy (e.g., "only from this specific SNS topic") |
| **Raw message delivery** | When off, SNS wraps messages in a JSON envelope with metadata |

---

Next: [Step 5 — Publish a message and verify fanout](./05-testing.md)
