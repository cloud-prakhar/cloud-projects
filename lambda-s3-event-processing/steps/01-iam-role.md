# Step 1 — IAM: Create the Lambda Execution Role

This function needs more permissions than a basic Hello World Lambda: it must read objects from the source bucket and write objects to the destination bucket, in addition to writing logs to CloudWatch.

You will create an execution role with the basic execution policy (logs) plus a scoped inline policy for S3.

---

## 1.1 Open IAM

1. In the AWS Console, search for **IAM** and open it.
2. In the left sidebar, click **Roles** → **Create role**.

---

## 1.2 Configure the Trust Policy

| Field | Value |
|-------|-------|
| Trusted entity type | **AWS service** |
| Use case | **Lambda** |

Click **Next**.

---

## 1.3 Attach Managed Policy

Search for `AWSLambdaBasicExecutionRole` and select the checkbox.

Click **Next**.

---

## 1.4 Name the Role

| Field | Value |
|-------|-------|
| Role name | `LambdaS3ProcessorRole` |
| Description | `Execution role for S3FileProcessor — CloudWatch Logs + scoped S3 access` |

Click **Create role**.

---

## 1.5 Get Your Account ID

You need your AWS account ID to build the bucket name and S3 ARNs. Find it in the top-right corner of the AWS Console (click your username → it's the 12-digit number), or run:

```bash
aws sts get-caller-identity --query Account --output text
```

Note it down — you'll use it throughout this project.

---

## 1.6 Add the S3 Inline Policy

1. Click on `LambdaS3ProcessorRole` to open it.
2. Click the **Permissions** tab → **Add permissions** → **Create inline policy**.
3. Click the **JSON** tab and paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::lambda-s3-source-YOUR_ACCOUNT_ID/*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::lambda-s3-dest-YOUR_ACCOUNT_ID/*"
    }
  ]
}
```

Replace `YOUR_ACCOUNT_ID` with your actual account ID (e.g., `279150584486`).

4. Click **Next**.
5. Policy name: `S3ReadWritePolicy`
6. Click **Create policy**.

> **Why inline?** Inline policies make the intent immediately visible on the role — you can see at a glance exactly which buckets this role can access. Managed policies are better for permissions shared across many roles.

---

## AWS CLI (Alternative)

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create role
aws iam create-role \
  --role-name LambdaS3ProcessorRole \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]
  }'

# Attach basic execution policy
aws iam attach-role-policy \
  --role-name LambdaS3ProcessorRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Add S3 inline policy
aws iam put-role-policy \
  --role-name LambdaS3ProcessorRole \
  --policy-name S3ReadWritePolicy \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {\"Effect\":\"Allow\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::lambda-s3-source-${ACCOUNT_ID}/*\"},
      {\"Effect\":\"Allow\",\"Action\":\"s3:PutObject\",\"Resource\":\"arn:aws:s3:::lambda-s3-dest-${ACCOUNT_ID}/*\"}
    ]
  }"
```

---

## Checkpoint

- [ ] Role `LambdaS3ProcessorRole` exists with `AWSLambdaBasicExecutionRole` attached
- [ ] Inline policy `S3ReadWritePolicy` is present with the two S3 statements
- [ ] You have noted your AWS account ID

---

**Next:** [Step 2 — Create the S3 Buckets](./02-s3-buckets.md)
