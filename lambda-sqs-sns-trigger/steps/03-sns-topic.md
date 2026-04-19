# Step 3 — SNS: Create Topics and Subscribe

You will create two SNS topics:

| Topic | Purpose |
|-------|---------|
| `OrderNotifications` | **Business events** — published on successful processing; consumed by fulfillment, inventory, etc. |
| `OrderAlerts` | **Operational alerts** — published on every success AND failure; consumed by operators and monitoring tools |

Separating concerns means a failed message alert doesn't land in the same topic as a downstream fulfillment event.

---

## 3.1 Create OrderNotifications Topic

1. In the AWS Console, search for **SNS** and open it.
2. In the left sidebar click **Topics** → **Create topic**.

| Field | Value |
|-------|-------|
| Type | **Standard** |
| Name | `OrderNotifications` |

Click **Create topic**.

3. Copy the **Topic ARN** — you will set this as `SNS_TOPIC_ARN` in the Lambda environment variables.

---

## 3.2 Create OrderAlerts Topic

1. Click **Create topic** again.

| Field | Value |
|-------|-------|
| Type | **Standard** |
| Name | `OrderAlerts` |

Click **Create topic**.

2. Copy the **Topic ARN** — you will set this as `ALERT_SNS_TOPIC_ARN` in the Lambda environment variables.

---

## 3.3 Subscribe Your Email to OrderAlerts

This gives you real-time visibility into every success and failure the Lambda processes.

1. With `OrderAlerts` open, click **Create subscription**.

| Field | Value |
|-------|-------|
| Protocol | **Email** |
| Endpoint | your email address |

Click **Create subscription**.

2. Check your inbox for a confirmation email from AWS and click **Confirm subscription**.

> You will not receive any alerts until you confirm. Check your spam folder if it does not arrive within a minute.

---

## 3.4 (Optional) Filter Alerts by Status

If you only want to receive failure emails — not one for every successful order — add a subscription filter policy:

1. SNS → `OrderAlerts` → **Subscriptions** → click your email subscription → **Edit**.
2. Under **Subscription filter policy** paste:

```json
{
  "status": ["FAILED"]
}
```

Click **Save changes**. Now your email only receives `FAILED` alerts; `SUCCESS` alerts are still published but filtered out for this subscriber.

> The `status` attribute is set by the Lambda function in `MessageAttributes` — `SUCCESS` or `FAILED` — so SNS can route them differently per subscriber.

---

## 3.5 Subscribe Your Email to OrderNotifications

This lets you see the business notification that downstream services would receive.

1. Open `OrderNotifications` → **Create subscription**.

| Field | Value |
|-------|-------|
| Protocol | **Email** |
| Endpoint | your email address |

Click **Create subscription** and confirm from your inbox.

---

## 3.6 Create a "ProcessedOrders" SQS Queue

This queue simulates a downstream service (e.g., a fulfillment system) consuming processed-order events.

1. Go to **SQS** → **Create queue**.

| Field | Value |
|-------|-------|
| Type | Standard |
| Name | `ProcessedOrders` |

Click **Create queue**.

2. Copy the **Queue ARN** for `ProcessedOrders`.

---

## 3.7 Subscribe ProcessedOrders Queue to OrderNotifications

1. Back in **SNS** → **Topics** → `OrderNotifications` → **Create subscription**.

| Field | Value |
|-------|-------|
| Protocol | **Amazon SQS** |
| Endpoint | ARN of `ProcessedOrders` |

Click **Create subscription**.

---

## 3.8 Add SQS Access Policy for SNS Delivery

SNS must be allowed to send messages to the `ProcessedOrders` queue.

1. Go to **SQS** → `ProcessedOrders` → **Access policy** tab → **Edit**.
2. Replace the existing policy with the following (substitute your values):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSNSPublish",
      "Effect": "Allow",
      "Principal": {
        "Service": "sns.amazonaws.com"
      },
      "Action": "sqs:SendMessage",
      "Resource": "<ProcessedOrders-Queue-ARN>",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "<OrderNotifications-Topic-ARN>"
        }
      }
    }
  ]
}
```

Click **Save**.

---

## What You Created

```
OrderNotifications (SNS Topic)  ← business events (success only)
  ├── Email subscription  → your inbox
  └── SQS subscription   → ProcessedOrders queue

OrderAlerts (SNS Topic)          ← ops visibility (success + failure)
  └── Email subscription  → your inbox
        (optional filter: status = FAILED)
```

---

**Next:** [Step 4 — Create the Lambda Function](./04-lambda-function.md)
