# Step 5 — Publish a Message and Verify Fanout

## What You're Testing

You will publish a single message to the `OrderEvents` SNS topic and verify that **both** SQS queues (`InventoryQueue` and `NotificationQueue`) receive a copy of the message independently. This is the fanout pattern in action.

---

## Step 5.1 — Publish a Message via SNS Console

1. Go to **SNS Console** → **Topics** → click `OrderEvents`
2. Click **Publish message**
3. Fill in the following:

   - **Subject (optional):** `New Order`
   - **Message body:**
     ```json
     {
       "orderId": "ORD-1001",
       "customerId": "CUST-42",
       "item": "Laptop",
       "quantity": 1,
       "totalAmount": 1299.99
     }
     ```

4. Leave **Message structure** as **Identical payload for all delivery protocols**
5. Click **Publish message**

You should see a green banner: **Message published successfully**, with a Message ID.

---

## Step 5.2 — Receive the Message from InventoryQueue

1. Go to **SQS Console** → click `InventoryQueue`
2. Click **Send and receive messages** (top right)
3. Scroll down to **Receive messages** → click **Poll for messages**
4. A message should appear in the table — click on it to view the body

   The message body will look like this (SNS envelope wrapping your order JSON):

   ```json
   {
     "Type": "Notification",
     "MessageId": "abc-123-...",
     "TopicArn": "arn:aws:sns:us-east-1:123456789012:OrderEvents",
     "Subject": "New Order",
     "Message": "{\n  \"orderId\": \"ORD-1001\",\n  \"customerId\": \"CUST-42\",\n  \"item\": \"Laptop\",\n  \"quantity\": 1,\n  \"totalAmount\": 1299.99\n}",
     "Timestamp": "2024-01-15T10:30:00.000Z",
     "SignatureVersion": "1",
     "Signature": "...",
     "SigningCertURL": "...",
     "UnsubscribeURL": "..."
   }
   ```

   > Notice: Your order JSON is inside the `"Message"` field as a string. This is the SNS envelope. The actual business payload is `Message`. A real consumer would parse the outer JSON, then parse `Message` again.

5. Close the message view
6. Click **Delete** on the message to acknowledge it

---

## Step 5.3 — Receive the Message from NotificationQueue

Repeat Step 5.2 for `NotificationQueue`.

You should see the **same message** (same content, same SNS MessageId) — confirming that both queues received an independent copy.

---

## Step 5.4 — Publish a Second Message and Observe

Try publishing another message without deleting it from the queue, and poll again. Observe:

- The message count in **Messages Available** increments
- Messages accumulate until a consumer deletes them
- If you don't delete a message within the visibility timeout, it reappears for another consumer

---

## Verification Checklist

- [ ] Published a message to `OrderEvents` SNS topic
- [ ] Polled `InventoryQueue` and received the message
- [ ] Polled `NotificationQueue` and received the same message
- [ ] Observed the SNS envelope JSON wrapping the original message body
- [ ] Deleted the message from both queues

---

## Key Concepts

| Concept | Explanation |
|---------|-------------|
| **Fanout** | One SNS publish → multiple SQS queues each get a copy |
| **SNS Envelope** | SNS wraps messages in JSON metadata before delivery to SQS |
| **Polling** | SQS consumers actively request messages (pull model), unlike SNS which pushes |
| **Message acknowledgment** | Deleting a message from SQS signals that it has been successfully processed |
| **Visibility Timeout** | The window in which a received message is hidden from other consumers |

---

Next: [Step 6 — Cleanup](./06-cleanup.md)
