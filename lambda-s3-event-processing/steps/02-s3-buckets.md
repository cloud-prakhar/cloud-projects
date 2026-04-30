# Step 2 — Create the S3 Buckets

You need two S3 buckets:

| Bucket | Role |
|--------|------|
| **Source** | Receives uploaded files; triggers Lambda |
| **Destination** | Receives Lambda's result JSON files |

The buckets are named with your account ID to guarantee global uniqueness (S3 bucket names are unique across all AWS accounts worldwide).

> **Why two buckets?** If Lambda read from and wrote to the same bucket, every result file it writes would trigger another Lambda invocation, creating an infinite loop. Two separate buckets completely eliminates this risk.

---

## 2.1 Note Your Account ID

You'll use it in the bucket names. From Step 1 you should have it already. If not:

```bash
aws sts get-caller-identity --query Account --output text
```

---

## 2.2 Create the Source Bucket

1. In the AWS Console, search for **S3** and open it.
2. Click **Create bucket**.

   | Field | Value |
   |-------|-------|
   | Bucket name | `lambda-s3-source-YOUR_ACCOUNT_ID` |
   | AWS Region | **US East (N. Virginia) us-east-1** |
   | Object Ownership | ACLs disabled (Bucket owner enforced) |
   | Block Public Access | Keep all four blocks **enabled** (default) |

3. Click **Create bucket**.

---

## 2.3 Create the Destination Bucket

1. Click **Create bucket** again.

   | Field | Value |
   |-------|-------|
   | Bucket name | `lambda-s3-dest-YOUR_ACCOUNT_ID` |
   | AWS Region | **US East (N. Virginia) us-east-1** |
   | Block Public Access | Keep all four blocks **enabled** |

2. Click **Create bucket**.

---

## 2.4 Verify Both Buckets

Back on the S3 console main page, search for `lambda-s3` in the bucket list. Both buckets should appear.

---

## AWS CLI (Alternative)

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws s3api create-bucket \
  --bucket "lambda-s3-source-${ACCOUNT_ID}" \
  --region us-east-1

aws s3api create-bucket \
  --bucket "lambda-s3-dest-${ACCOUNT_ID}" \
  --region us-east-1

# Verify
aws s3api list-buckets \
  --query "Buckets[?contains(Name,'lambda-s3')].Name" \
  --output table
```

> For regions other than us-east-1, add `--create-bucket-configuration LocationConstraint=REGION` to each command.

---

## Checkpoint

- [ ] Source bucket `lambda-s3-source-<your-account-id>` created in us-east-1
- [ ] Destination bucket `lambda-s3-dest-<your-account-id>` created in us-east-1
- [ ] Both buckets have public access blocked

---

**Next:** [Step 3 — Deploy the Lambda Function](./03-lambda-function.md)
