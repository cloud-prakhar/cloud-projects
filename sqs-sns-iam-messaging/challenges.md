# Challenges

These challenges extend the core project. Each one introduces a real-world concept or AWS feature. Work through them after completing all six steps.

---

## Challenge 1 — Dead Letter Queue (DLQ)

**Concept:** What happens when a consumer fails to process a message repeatedly? In production, you don't want messages silently dropped. A Dead Letter Queue (DLQ) captures messages that exceed the maximum receive count.

**Task:**
1. Create a new SQS Standard queue named `InventoryDLQ`
2. Configure `InventoryQueue` to use `InventoryDLQ` as its dead letter queue with a **maxReceiveCount of 3**
3. Poll `InventoryQueue` three times **without deleting the message** each time
4. After the third receive, check `InventoryDLQ` — the message should have moved there automatically

**What to look for:** Navigate to `InventoryQueue` → **Dead-letter queue** tab to configure it. After completing, observe the message count in `InventoryDLQ`.

**Key question:** Why is a DLQ important in production systems?

---

## Challenge 2 — Message Filtering

**Concept:** SNS subscription filter policies let each subscriber receive only the messages relevant to them — rather than receiving every message published to the topic.

**Task:**
1. Add a **subscription filter policy** to the `InventoryQueue` subscription so it only receives messages where the item is `"Laptop"`
2. Publish two messages to `OrderEvents` — one with `"item": "Laptop"` and one with `"item": "Headphones"`
3. Poll `InventoryQueue` — only the Laptop message should appear
4. Poll `NotificationQueue` — both messages should appear (no filter)

**Where to set it:** SNS → Topics → OrderEvents → Subscriptions → click the InventoryQueue subscription → **Edit** → **Subscription filter policy**

Example filter policy:
```json
{
  "item": ["Laptop"]
}
```

**Key question:** How does filtering help reduce processing load on consumers?

---

## Challenge 3 — Tighten the IAM Policy

**Concept:** The policy created in Step 1 grants access to all SNS and SQS resources (`"Resource": "*"`). In production, you scope policies to specific resource ARNs.

**Task:**
1. Edit `MessagingLabPolicy` to replace `"Resource": "*"` with the specific ARNs of the resources you created:
   - The `OrderEvents` SNS topic ARN
   - The `InventoryQueue` SQS ARN
   - The `NotificationQueue` SQS ARN
2. Test that the user can still publish to `OrderEvents` and receive from both queues
3. Attempt to create a **new** SNS topic — confirm it fails with AccessDenied

**Key question:** Why is scoping policies to specific ARNs better than using wildcards?

---

## Challenge 4 — Add an Email Subscriber

**Concept:** SNS supports multiple protocol types on the same topic simultaneously. You can add an email subscriber alongside the existing SQS subscribers.

**Task:**
1. Add a new subscription to `OrderEvents` with **Protocol: Email** and your email address as the endpoint
2. Confirm the subscription via the email you receive (subscription confirmation link)
3. Publish a message to `OrderEvents`
4. Verify that you receive the email **and** both SQS queues receive the message

**Key question:** What is the delivery guarantee difference between email and SQS subscribers?

---

## Challenge 5 — FIFO Topic and Queue

**Concept:** Standard SNS/SQS guarantees at-least-once delivery with no ordering guarantee. FIFO (First-In-First-Out) guarantees strict ordering and exactly-once processing — important for financial transactions, inventory updates, and other order-sensitive workflows.

**Task:**
1. Create a new SNS topic named `OrderEventsFIFO` with **Type: FIFO** (name must end in `.fifo`)
2. Create a new SQS queue named `InventoryQueueFIFO.fifo` with **Type: FIFO**
3. Subscribe the FIFO queue to the FIFO topic
4. Publish 5 messages with a **Message Group ID** of `order-group-1`
5. Poll the FIFO queue and observe that messages arrive in the exact order they were published

**Key question:** When would you choose FIFO over Standard, and what trade-offs do you accept?

---

## Challenge 6 — Observe the SNS Envelope vs. Raw Delivery

**Concept:** When raw message delivery is disabled (default), SNS wraps messages in a JSON envelope. When enabled, the raw message body is delivered directly. This affects how consumers parse messages.

**Task:**
1. Edit the `InventoryQueue` subscription and **enable raw message delivery**
2. Publish a message to `OrderEvents`
3. Poll `InventoryQueue` — compare the message body to what you saw in Step 5

   Without raw delivery → you see the full SNS envelope JSON  
   With raw delivery → you see only the message body you published

4. Edit the subscription again and **disable** raw delivery
5. Publish another message and confirm the envelope is back

**Key question:** When would a consumer prefer raw delivery? When would it want the envelope?
