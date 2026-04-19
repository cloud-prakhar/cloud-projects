# Troubleshooting

Common errors encountered in this project and how to resolve them.

---

## Messages Not Appearing in SQS Queue

**Symptom:** You published a message to SNS but polling the SQS queue returns nothing.

**Causes and fixes:**

| Cause | How to Check | Fix |
|-------|-------------|-----|
| SQS access policy not updated | Go to SQS → queue → Access policy tab | Add the `AllowSNSDelivery` statement from Step 4.3 |
| Subscription not confirmed | SNS → Topics → OrderEvents → Subscriptions tab | Status must be **Confirmed**. If Pending, delete and recreate the subscription |
| Wrong region | Check that SNS topic and SQS queues are in the same AWS region | Recreate resources in the same region |
| Subscription endpoint ARN is wrong | SNS → Subscriptions → check the Endpoint ARN | Verify it matches the SQS queue ARN exactly |

---

## Error: `AuthorizationError` When Publishing to SNS

**Symptom:** Clicking "Publish message" shows an access denied or authorization error.

**Cause:** The IAM user does not have `sns:Publish` permission.

**Fix:**
1. Go to **IAM → Policies → MessagingLabPolicy**
2. Verify `sns:Publish` is in the `Action` list
3. If missing, edit the policy and add it
4. Wait ~30 seconds and retry

---

## Error: `InvalidClientTokenId` or `AccessDenied` on Login

**Symptom:** The IAM user cannot log in to the console or sees access denied.

**Fix:**
1. Confirm you are using the correct sign-in URL: `https://<account-id>.signin.aws.amazon.com/console`
2. Verify the password is correct (reset in IAM if needed)
3. Confirm the user has console access enabled (IAM → Users → Security credentials)

---

## SQS Queue Shows `Messages Available: 0` After Polling

**Symptom:** You polled the queue but no messages appeared, and you know a message was sent.

**Possible causes:**

1. **Message already deleted:** If you or someone else already received and deleted the message, it is gone.
2. **Message in flight:** If a message was received but not deleted within the visibility timeout, it returns to the queue — wait 30 seconds and poll again.
3. **Short poll returned nothing:** SQS short polling only queries a subset of servers. Try polling again — the message may appear on the next request.

---

## Error: `AWS.SimpleQueueService.NonExistentQueue`

**Symptom:** You receive this error when trying to send or receive messages.

**Cause:** The queue URL or name is incorrect, or the queue is in a different region.

**Fix:**
1. Go to **SQS Console** and copy the Queue URL directly from the queue details page
2. Confirm the region in the URL matches your console region

---

## SNS Subscription Status Shows `PendingConfirmation`

**Symptom:** After creating an SQS subscription, the status shows `PendingConfirmation` instead of `Confirmed`.

**Cause:** This typically happens when the SQS queue's access policy does not allow SNS to send messages to it. SNS could not deliver the subscription confirmation message.

**Fix:**
1. Update the SQS access policy as described in Step 4.3
2. Delete the pending subscription
3. Recreate the subscription — it should auto-confirm immediately

---

## IAM Policy Changes Not Taking Effect

**Symptom:** You updated an IAM policy but still see access denied errors.

**Cause:** IAM policy changes propagate within seconds, but cached credentials in active sessions may not reflect changes immediately.

**Fix:** Sign out and sign back in as the IAM user, or wait up to 60 seconds.

---

## Deleted Queue Name Conflict

**Symptom:** After deleting an SQS queue, trying to recreate it with the same name fails.

**Cause:** AWS requires a 60-second wait after deleting a Standard queue before the name can be reused.

**Fix:** Wait 60 seconds and try again, or use a slightly different name temporarily.
