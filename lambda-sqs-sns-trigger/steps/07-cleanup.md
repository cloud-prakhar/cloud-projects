# Step 7 — Cleanup: Delete All Resources

Delete resources in this order to avoid dependency errors.

---

## 7.1 Delete the Lambda Event Source Mapping

1. Open **Lambda** → `OrderProcessor` → **Configuration** → **Triggers**.
2. Select the SQS trigger → **Delete**.

---

## 7.2 Delete the Lambda Function

1. Go to **Lambda** → **Functions**.
2. Select `OrderProcessor` → **Actions** → **Delete**.
3. Type `delete` to confirm.

---

## 7.3 Delete the SNS Subscriptions and Topics

1. Go to **SNS** → **Subscriptions**.
2. Select all subscriptions for `OrderNotifications` (email + SQS) → **Delete**.
3. Select the email subscription for `OrderAlerts` → **Delete**.
4. Go to **SNS** → **Topics**.
5. Select `OrderNotifications` → **Delete** → type `delete me` to confirm.
6. Select `OrderAlerts` → **Delete** → type `delete me` to confirm.

---

## 7.4 Delete the SQS Queues

1. Go to **SQS**.
2. Select `OrderQueue` → **Delete** → confirm.
3. Select `ProcessedOrders` → **Delete** → confirm.
4. Select `OrderDLQ` → **Delete** → confirm.

---

## 7.5 Delete the IAM Role

1. Go to **IAM** → **Roles**.
2. Search for `OrderProcessorLambdaRole`.
3. Select it → **Delete** → type the role name to confirm.

---

## 7.6 Delete CloudWatch Log Group

Lambda automatically creates a log group. To delete it:

1. Go to **CloudWatch** → **Log groups**.
2. Find `/aws/lambda/OrderProcessor`.
3. Select it → **Actions** → **Delete log group(s)** → confirm.

---

## Verification

After cleanup, verify:
- Lambda console shows no `OrderProcessor` function
- SQS console shows none of the three queues (`OrderQueue`, `OrderDLQ`, `ProcessedOrders`)
- SNS console shows neither `OrderNotifications` nor `OrderAlerts`
- IAM console shows no `OrderProcessorLambdaRole`

You will not be charged for any of the resources used in this project if they are deleted promptly.
