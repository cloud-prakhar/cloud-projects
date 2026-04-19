# Step 2 — SQS: Create OrderQueue and Dead-Letter Queue

You will create two queues:
- **OrderDLQ** — receives messages that Lambda fails to process after several attempts
- **OrderQueue** — the main inbound queue; Lambda is triggered by messages here

Create the DLQ first because the main queue references it.

---

## 2.1 Create the Dead-Letter Queue (OrderDLQ)

1. In the AWS Console, search for **SQS** and open it.
2. Click **Create queue**.

| Field | Value |
|-------|-------|
| Type | Standard |
| Name | `OrderDLQ` |

Leave all other settings at their defaults and click **Create queue**.

3. Copy the **Queue ARN** for `OrderDLQ` — you will need it in the next section.

---

## 2.2 Create the Main Queue (OrderQueue)

1. Click **Create queue** again.

| Field | Value |
|-------|-------|
| Type | Standard |
| Name | `OrderQueue` |

2. Scroll down to **Dead-letter queue** and expand it.

| Field | Value |
|-------|-------|
| Dead-letter queue | **Enabled** |
| Choose queue | `OrderDLQ` (paste the ARN you copied) |
| Maximum receives | `3` |

> **Maximum receives = 3** means: if the same message is received and not deleted 3 times (Lambda threw an exception each time), SQS moves it to the DLQ automatically.

3. Leave all other settings at defaults. Click **Create queue**.

4. Copy the **Queue URL** and **Queue ARN** for `OrderQueue` — you will need these in later steps.

---

## What You Created

```
OrderQueue (Standard)
  └── Dead-letter queue → OrderDLQ (maxReceiveCount: 3)
```

When Lambda fails to process a message 3 times, SQS automatically moves it to `OrderDLQ` so it isn't lost and can be investigated.

---

**Next:** [Step 3 — Create SNS Topic](./03-sns-topic.md)
