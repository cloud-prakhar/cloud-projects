# Step 6 — Cleanup: Delete All Resources

## Why Cleanup Matters

Even though the services used in this project are within the AWS Free Tier, it is good practice to delete resources when you are done. Leaving unused resources in your account can lead to unexpected charges and clutters your environment.

**Delete resources in this order** — some resources depend on others.

---

## Step 6.1 — Delete SNS Subscriptions

1. Go to **SNS Console** → **Subscriptions** (left sidebar)
2. Select the subscription for `InventoryQueue` → click **Delete** → confirm
3. Select the subscription for `NotificationQueue` → click **Delete** → confirm

---

## Step 6.2 — Delete the SNS Topic

1. Go to **SNS Console** → **Topics**
2. Select `OrderEvents` → click **Delete**
3. Type `delete me` in the confirmation box → click **Delete**

---

## Step 6.3 — Delete the SQS Queues

1. Go to **SQS Console**
2. Select `InventoryQueue` → click **Delete** → type `delete` to confirm
3. Select `NotificationQueue` → click **Delete** → type `delete` to confirm

> **Note:** SQS queue deletion may take up to 60 seconds to complete fully. The queue name cannot be reused for 60 seconds after deletion.

---

## Step 6.4 — Delete the IAM User and Policy

### Delete the IAM User:

1. Go to **IAM Console** → **Users**
2. Click `messaging-lab-user`
3. Click **Delete** → type the username to confirm → **Delete**

### Delete the IAM Policy:

1. Go to **IAM Console** → **Policies**
2. Search for `MessagingLabPolicy`
3. Click the policy → **Actions** → **Delete** → confirm

---

## Verification

- **SNS Console → Topics:** No `OrderEvents` topic
- **SNS Console → Subscriptions:** No subscriptions remaining
- **SQS Console:** No `InventoryQueue` or `NotificationQueue`
- **IAM Console → Users:** No `messaging-lab-user`
- **IAM Console → Policies:** No `MessagingLabPolicy` under Customer managed

---

## Cleanup Checklist

- [ ] Deleted both SNS subscriptions
- [ ] Deleted the `OrderEvents` SNS topic
- [ ] Deleted `InventoryQueue`
- [ ] Deleted `NotificationQueue`
- [ ] Deleted IAM user `messaging-lab-user`
- [ ] Deleted IAM policy `MessagingLabPolicy`
