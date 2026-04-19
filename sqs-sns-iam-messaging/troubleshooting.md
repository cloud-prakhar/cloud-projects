# Troubleshooting

Common errors encountered in this project and how to resolve them.

---

## Messages Not Appearing in SQS Queue

**Symptom:** You published a message to SNS but polling the SQS queue returns nothing.

**Causes and fixes:**

| Cause | How to Check | Fix |
|-------|-------------|-----|
| SQS access policy not updated | SQS → queue → Access policy tab | Add the `AllowSNSDelivery` statement from Step 4.3 |
| Subscription not confirmed | SNS → Topics → OrderEvents → Subscriptions tab | Status must be **Confirmed**. If Pending, see section below |
| Wrong region | Check that SNS topic and SQS queues are in the same AWS region | Recreate resources in the same region |
| Subscription endpoint ARN is wrong | SNS → Subscriptions → check the Endpoint ARN | Verify it matches the SQS queue ARN exactly |

---

## SNS Subscription Status Shows `PendingConfirmation`

**Symptom:** After subscribing an SQS queue to SNS, the status shows `PendingConfirmation` instead of `Confirmed`.

**Cause:** The SQS queue's access policy does not allow SNS to send messages to it. SNS attempted to deliver a subscription confirmation message to verify ownership — the queue rejected it, so the subscription never auto-confirmed.

> Unlike email subscriptions (which always require a manual click), SQS subscriptions auto-confirm the moment SNS can successfully deliver a message to the queue. The access policy must be in place **before** or **at the time** you create the subscription.

**Fix:**
1. Update the SQS access policy as described in Step 4.3
2. Delete the pending subscription (SNS → Subscriptions → select → Delete)
3. Recreate the subscription — it will auto-confirm immediately because the policy is now correct

---

## Error: `AuthorizationError` When Publishing to SNS

**Symptom:** Clicking "Publish message" shows an access denied or authorization error.

**Cause:** The IAM user does not have `sns:Publish` permission.

**Fix:**
1. Go to **IAM → Policies → MessagingLabPolicy**
2. Verify `sns:Publish` is in the `Action` list
3. If missing, edit the policy and add it
4. Sign out and sign back in as the IAM user to pick up the updated policy

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
2. **Message in flight:** If a message was received but not deleted within the visibility timeout (default: 30 seconds), it is hidden. Wait 30 seconds and poll again.
3. **Short poll sampled the wrong servers:** SQS distributes messages across multiple servers. A short poll (the default in the console) queries only a random subset — it can return empty even when messages exist. Poll 2–3 more times; the message will appear. For guaranteed retrieval use long polling (WaitTimeSeconds = 20), which queries all servers.

---

## Error: `AWS.SimpleQueueService.NonExistentQueue`

**Symptom:** You receive this error when trying to send or receive messages.

**Cause:** The queue URL or name is incorrect, or the queue is in a different region.

**Fix:**
1. Go to **SQS Console** and copy the Queue URL directly from the queue details page
2. Confirm the region in the URL matches your console region (`us-east-1`, `eu-west-1`, etc.)

---

## IAM Policy Changes Not Taking Effect

**Symptom:** You updated an IAM policy but still see access denied errors.

**Cause:** IAM policy changes propagate within seconds, but an active console session may cache your previous permissions.

**Fix:** Sign out and sign back in as the IAM user.

---

## Deleted Queue Name Conflict

**Symptom:** After deleting an SQS queue, trying to recreate it with the same name fails immediately.

**Cause:** AWS requires a **60-second wait** after deleting a Standard queue before the name can be reused. The old queue's metadata is still being purged.

**Fix:** Wait 60 seconds and try again, or use a slightly different name (e.g. `InventoryQueue2`) temporarily.

---

## Only One Queue Received the SNS Message

**Symptom:** After publishing to SNS, `InventoryQueue` has a message but `NotificationQueue` does not (or vice versa).

**Possible causes:**

1. **Only one subscription was created:** SNS → Topics → OrderEvents → Subscriptions tab — verify both queues appear as separate subscriptions with status **Confirmed**.
2. **Access policy missing on one queue:** Each queue needs its own `AllowSNSDelivery` policy statement. Check both queues individually under SQS → queue → Access policy.
3. **Message already polled from one queue:** If you polled and deleted the message from one queue before checking the other, it is gone. Publish a new test message.
