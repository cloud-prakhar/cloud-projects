# Step 1 — IAM Setup: Create a Least-Privilege User

## Why This Matters

Rather than using your root account or an admin user, you will create a dedicated IAM user with only the permissions needed for this project. This reflects real-world best practice: **grant the minimum permissions required, nothing more.**

---

## What You'll Create

- An IAM user named `messaging-lab-user`
- A custom IAM policy that allows only the SNS and SQS actions needed
- An access key to use with the AWS Console (console password)

---

## Step 1.1 — Create the IAM Policy

1. Open the [IAM Console](https://console.aws.amazon.com/iam/)
2. In the left sidebar, click **Policies** → **Create policy**
3. Click the **JSON** tab and paste the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SNSPermissions",
      "Effect": "Allow",
      "Action": [
        "sns:CreateTopic",
        "sns:DeleteTopic",
        "sns:Publish",
        "sns:Subscribe",
        "sns:Unsubscribe",
        "sns:ListTopics",
        "sns:GetTopicAttributes",
        "sns:SetTopicAttributes",
        "sns:ListSubscriptionsByTopic"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SQSPermissions",
      "Effect": "Allow",
      "Action": [
        "sqs:CreateQueue",
        "sqs:DeleteQueue",
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:SetQueueAttributes",
        "sqs:GetQueueUrl",
        "sqs:ListQueues"
      ],
      "Resource": "*"
    }
  ]
}
```

4. Click **Next**
5. Name the policy: `MessagingLabPolicy`
6. Click **Create policy**

> **What this policy does:** It allows SNS publish/subscribe operations and SQS send/receive/delete operations. It does **not** allow any other AWS services — for example, S3, EC2, or Lambda cannot be accessed with this policy.

---

## Step 1.2 — Create the IAM User

1. In the left sidebar, click **Users** → **Create user**
2. Username: `messaging-lab-user`
3. Check **Provide user access to the AWS Management Console**
4. Select **I want to create an IAM user**
5. Set a custom password (note it down)
6. Uncheck "Users must create a new password at next sign-in"
7. Click **Next**

---

## Step 1.3 — Attach the Policy

1. On the **Set permissions** page, choose **Attach policies directly**
2. Search for `MessagingLabPolicy` and check the box next to it
3. Click **Next** → **Create user**

---

## Step 1.4 — Save the Console Sign-In URL

1. After creating the user, click **Return to users list**
2. At the top of the IAM dashboard, note your **Account ID** (12-digit number)
3. The sign-in URL for IAM users is:
   ```
   https://<your-account-id>.signin.aws.amazon.com/console
   ```

---

## Verification

- Navigate to **Users** → click `messaging-lab-user`
- Under the **Permissions** tab, confirm `MessagingLabPolicy` is attached
- Under the **Security credentials** tab, confirm the console password is set

---

## Key Concepts

| Concept | Explanation |
|---------|-------------|
| **Least privilege** | Users should only have the permissions they need — no more |
| **IAM Policy** | A JSON document that defines what actions are allowed or denied |
| **IAM User** | A person or application identity in AWS with long-term credentials |
| **Managed Policy** | A standalone policy that can be attached to multiple users/roles |

---

Next: [Step 2 — Create the SNS Topic](./02-sns-topic.md)
