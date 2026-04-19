# Step 6 — Testing: Send a Message and Verify the Pipeline

You will send a test order to `OrderQueue` and verify that Lambda processes it and SNS delivers notifications.

---

## 6.1 Send a Test Message via the Console

1. In the AWS Console, go to **SQS** → `OrderQueue`.
2. Click **Send and receive messages** → **Send message**.
3. Paste this JSON into the **Message body** field:

```json
{
  "orderId": "ORD-001",
  "customer": "Jane Doe",
  "amount": 49.99,
  "items": ["Widget A", "Widget B"]
}
```

4. Click **Send message**.

---

## 6.2 Send a Test Message via AWS CLI

If you have the AWS CLI configured:

```bash
aws sqs send-message \
  --queue-url <OrderQueue-URL> \
  --message-body '{"orderId":"ORD-002","customer":"John Smith","amount":129.00,"items":["Gadget X"]}'
```

Replace `<OrderQueue-URL>` with the URL you copied in Step 2.

---

## 6.3 Verify Lambda Was Invoked

1. Open **Lambda** → `OrderProcessor` → **Monitor** tab → **View CloudWatch logs**.
2. Click the most recent log stream.

You should see log lines similar to:

```
Published SNS notification for order ORD-001
Processed: 1, Failed: 0
```

---

## 6.4 Verify Email Notification

Check the inbox you subscribed in Step 3. You should receive an email with:
- **Subject:** `Order Processed: ORD-001`
- **Body:** JSON with `status: "PROCESSED"` and order details

> It may take up to 60 seconds to arrive.

---

## 6.5 Verify ProcessedOrders Queue

1. Go to **SQS** → `ProcessedOrders`.
2. Click **Send and receive messages** → **Poll for messages**.
3. You should see a message. Click on it to inspect the body — it will contain the SNS envelope wrapping the notification JSON.

---

## 6.6 Test a Failure (DLQ Path)

Send a malformed message to verify the DLQ works:

```bash
aws sqs send-message \
  --queue-url <OrderQueue-URL> \
  --message-body 'this is not valid json'
```

Lambda will fail to `json.loads` this body. After 3 receive attempts (maxReceiveCount), SQS moves it to `OrderDLQ`.

Verify:
1. Wait ~2 minutes (SQS visibility timeout + retries).
2. Go to **SQS** → `OrderDLQ` → **Send and receive messages** → **Poll for messages**.
3. The malformed message should appear there.

---

## 6.7 Lambda Test Event (Console)

You can also test directly from the Lambda console without sending an SQS message:

1. Open `OrderProcessor` → **Test** tab → **Create new event**.
2. Select **Template** → search for `sqs` → choose **SQS**.
3. Replace the `body` field in the template with:

```json
"{\"orderId\":\"ORD-TEST\",\"customer\":\"Test User\",\"amount\":9.99}"
```

4. Click **Test**. Check the **Execution results** and CloudWatch logs.

---

**Next:** [Step 7 — Cleanup](./07-cleanup.md)
