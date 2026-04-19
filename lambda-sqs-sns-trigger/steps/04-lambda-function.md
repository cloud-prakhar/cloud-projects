# Step 4 — Lambda: Create and Deploy the Function

You will create the Lambda function, upload the code, and set the SNS topic ARN as an environment variable.

---

## 4.1 Open Lambda

1. In the AWS Console, search for **Lambda** and open it.
2. Click **Create function**.

---

## 4.2 Basic Configuration

| Field | Value |
|-------|-------|
| Author from scratch | selected |
| Function name | `OrderProcessor` |
| Runtime | **Python 3.14** |
| Architecture | x86_64 |

---

## 4.3 Attach the Execution Role

Under **Permissions → Change default execution role**:

| Field | Value |
|-------|-------|
| Execution role | **Use an existing role** |
| Existing role | `OrderProcessorLambdaRole` (created in Step 1) |

Click **Create function**.

---

## 4.4 Upload the Code

The Lambda code is at [`../lambda/handler.py`](../lambda/handler.py) in this repo.

**Option A — Inline editor (quickest for this project):**

1. On the function page, scroll to the **Code source** section.
2. Click on `lambda_function.py` in the file tree and delete its contents.
3. Paste the entire contents of `handler.py` into the editor.
4. Click **Deploy**.

**Option B — ZIP upload:**

```bash
cd lambda-sqs-sns-trigger/lambda
zip function.zip handler.py
```

1. On the function page → **Upload from** → **.zip file** → select `function.zip`.
2. Click **Save**.

> **Note:** If you use Option A, the handler is `lambda_function.lambda_handler` by default. You need to change it to match the file name you pasted into. Either rename the file to `lambda_function.py` **or** update the handler setting (next section).

---

## 4.5 Set the Handler

If you pasted the code into `lambda_function.py` (the default file), no change is needed.

If you uploaded `handler.py`:

1. Click **Configuration** tab → **General configuration** → **Edit**.
2. Set **Handler** to `handler.lambda_handler`.
3. Click **Save**.

---

## 4.6 Set Environment Variables

1. Click **Configuration** tab → **Environment variables** → **Edit**.
2. Add both variables using **Add environment variable**:

| Key | Value | Required |
|-----|-------|----------|
| `SNS_TOPIC_ARN` | ARN of `OrderNotifications` (copied in Step 3.1) | Yes |
| `ALERT_SNS_TOPIC_ARN` | ARN of `OrderAlerts` (copied in Step 3.2) | Optional — if omitted, alerts are skipped and only CloudWatch logs are written |

Click **Save**.

> **Why two topics?** `SNS_TOPIC_ARN` carries business events consumed by downstream services. `ALERT_SNS_TOPIC_ARN` carries operational signals (success + failure) for operators and monitoring — keeping these separate means a processing failure doesn't pollute your fulfillment topic.

---

## 4.7 (Optional) Tune Memory and Timeout

The defaults (128 MB memory, 3-second timeout) are fine for this project. For real workloads, adjust under **Configuration → General configuration**.

---

## What You Deployed

The function:
1. Receives an SQS batch of records
2. Parses each record as a JSON order
3. On success: publishes the processed order to `OrderNotifications`; publishes a `SUCCESS` alert to `OrderAlerts`
4. On failure: publishes a `FAILED` alert to `OrderAlerts` with the error message and raw SQS body; returns the message ID in `batchItemFailures` so SQS retries only that record

---

**Next:** [Step 5 — Wire SQS to Lambda (Event Source Mapping)](./05-event-source-mapping.md)
