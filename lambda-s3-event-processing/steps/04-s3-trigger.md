# Step 4 — Configure the S3 Event Trigger

Connecting S3 to Lambda requires two things:

1. **A resource-based policy on Lambda** — grants S3 permission to invoke your function
2. **An event notification on the S3 source bucket** — tells S3 to call Lambda when objects are created

Both must be configured. If either is missing, S3 silently fails to invoke the function.

---

## 4.1 Grant S3 Permission to Invoke Lambda

S3 is a different AWS service calling your function. For cross-service invocations, Lambda uses **resource-based policies** (attached to the function itself) rather than IAM roles.

### Via Console

1. Open **Lambda → S3FileProcessor**.
2. Click the **Configuration** tab → **Permissions**.
3. Scroll to **Resource-based policy statements** → **Add permissions**.

   | Field | Value |
   |-------|-------|
   | Policy statement type | **AWS service** |
   | Service | **S3** |
   | Statement ID | `AllowS3Invoke` |
   | Principal | `s3.amazonaws.com` |
   | Source ARN | `arn:aws:s3:::lambda-s3-source-YOUR_ACCOUNT_ID` |
   | Source account | `YOUR_ACCOUNT_ID` |
   | Action | `lambda:InvokeFunction` |

4. Click **Save**.

> **`Source account` is important** — it prevents another account's bucket with the same name from invoking your function.

### Via CLI

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws lambda add-permission \
  --function-name S3FileProcessor \
  --statement-id AllowS3Invoke \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::lambda-s3-source-${ACCOUNT_ID}" \
  --source-account "$ACCOUNT_ID"
```

---

## 4.2 Configure the S3 Event Notification

### Via Console

1. Open **S3 → lambda-s3-source-YOUR_ACCOUNT_ID**.
2. Click the **Properties** tab → scroll to **Event notifications** → **Create event notification**.

   | Field | Value |
   |-------|-------|
   | Event name | `TriggerFileProcessor` |
   | Prefix | `uploads/` |
   | Event types | ✅ **All object create events** |
   | Destination | **Lambda function** |
   | Lambda function | `S3FileProcessor` |

3. Click **Save changes**.

> **Why the `uploads/` prefix filter?** Lambda writes results under `results/` in the destination bucket. If both trigger and write used the same bucket without a prefix filter, the result file could trigger another invocation. The prefix filter is a second safety net on top of using separate buckets.

### Via CLI

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
FUNCTION_ARN="arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:S3FileProcessor"

aws s3api put-bucket-notification-configuration \
  --bucket "lambda-s3-source-${ACCOUNT_ID}" \
  --notification-configuration "{
    \"LambdaFunctionConfigurations\": [{
      \"LambdaFunctionArn\": \"${FUNCTION_ARN}\",
      \"Events\": [\"s3:ObjectCreated:*\"],
      \"Filter\": {\"Key\": {\"FilterRules\": [{\"Name\": \"prefix\",\"Value\": \"uploads/\"}]}}
    }]
  }"
```

---

## 4.3 Verify the Notification Is Configured

In the S3 console on the **Properties** tab, scroll to **Event notifications** — you should see `TriggerFileProcessor` listed with status **Enabled**.

```bash
# Via CLI
aws s3api get-bucket-notification-configuration \
  --bucket "lambda-s3-source-$(aws sts get-caller-identity --query Account --output text)"
```

---

## How the Trigger Works

```
Upload to s3://source/uploads/file.txt
        │
        ▼
S3 checks event notification config
        │
Prefix matches "uploads/"? ──Yes──▶  S3 calls Lambda asynchronously
                                       Lambda reads the file and writes result
```

S3 invokes Lambda **asynchronously** — S3 does not wait for Lambda to finish. If Lambda errors, Lambda will retry up to 2 more times by default before giving up (or sending to a DLQ, covered in Project 4).

> **Sandbox note:** In restricted AWS sandbox accounts, S3 event notifications may not fire due to account-level SCP restrictions. If uploads do not trigger Lambda automatically after 60 seconds, use the manual invocation method from Step 3 to continue testing the code. See [troubleshooting.md](../troubleshooting.md) for details.

---

## Checkpoint

- [ ] Lambda resource policy shows `s3.amazonaws.com` as allowed principal
- [ ] Source bucket has an event notification pointing to `S3FileProcessor`
- [ ] Notification uses prefix filter `uploads/`

---

**Next:** [Step 5 — Testing](./05-testing.md)
