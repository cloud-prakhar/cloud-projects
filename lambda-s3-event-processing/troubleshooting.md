# Troubleshooting — Lambda S3 Event Processing

---

## S3 auto-trigger not firing in sandbox or restricted accounts

**Symptom:** Files upload to the source bucket successfully, but Lambda is never invoked — no new log streams appear in CloudWatch even after 60 seconds.

**Cause:** AWS sandbox and restricted accounts often have **Service Control Policies (SCPs)** at the organization level that block S3 event notifications from invoking Lambda, or have very low `ConcurrentExecutions` limits that cause silent throttling of async S3 invocations.

**Verification:** Check your account's concurrent execution limit:

```bash
aws lambda get-account-settings \
  --query 'AccountLimit.ConcurrentExecutions'
```

A value of `10` or below indicates a restricted sandbox account.

**Workaround:** Use the **manual invocation** method from Step 3 to test all functionality. The S3 processor code, IAM role, and bucket configuration are all correct — only the S3→Lambda event delivery path is blocked.

```bash
# Craft a synthetic S3 event and invoke manually
cat > /tmp/s3_event.json << 'EOF'
{
  "Records": [{
    "s3": {
      "bucket": { "name": "lambda-s3-source-YOUR_ACCOUNT_ID" },
      "object": { "key": "uploads/your-file.txt", "size": 100 }
    }
  }]
}
EOF

aws lambda invoke \
  --function-name S3FileProcessor \
  --cli-binary-format raw-in-base64-out \
  --payload file:///tmp/s3_event.json \
  response.json && cat response.json
```

In a production (unrestricted) AWS account, the S3 auto-trigger works correctly with the same configuration.

---

## Lambda is not invoked when I upload a file (general checklist)

Work through this checklist in order:

**1. Is the file in the correct prefix?**

```bash
# Upload to uploads/ — should trigger Lambda
aws s3 cp myfile.txt "s3://${SOURCE_BUCKET}/uploads/myfile.txt"

# Upload to root — should NOT trigger (prefix filter blocks it)
aws s3 cp myfile.txt "s3://${SOURCE_BUCKET}/myfile.txt"
```

**2. Is the event notification configured?**

```bash
aws s3api get-bucket-notification-configuration --bucket "$SOURCE_BUCKET"
```

If the output is `{}`, the notification was never set (or was cleared). Re-run Step 4.

**3. Does Lambda's resource policy allow S3 to invoke it?**

```bash
aws lambda get-policy --function-name S3FileProcessor \
  --query 'Policy' --output text | python3 -m json.tool
```

Look for a statement with `"Service": "s3.amazonaws.com"`. If missing, re-run the `add-permission` command from Step 4.

**4. Is the function in an error state?**

```bash
aws lambda get-function \
  --function-name S3FileProcessor \
  --query 'Configuration.State'
```

If `State = "Failed"`, the function has a configuration problem (usually a bad IAM role). Check the role ARN.

---

## Error: `NoSuchKey` when Lambda tries to read the file

**Symptom:** CloudWatch shows `NoSuchKey` or `The specified key does not exist`.

**Cause 1:** The key in the event payload is URL-encoded but your code uses it as-is.

**Fix:** Ensure you're calling `urllib.parse.unquote_plus(record["s3"]["object"]["key"])` before using the key.

**Cause 2:** The function's IAM role can access the destination bucket but not the source bucket (or vice versa).

**Fix:** Check the inline policy:

```bash
aws iam get-role-policy \
  --role-name LambdaS3ProcessorRole \
  --policy-name S3ReadWritePolicy
```

Verify `s3:GetObject` points to the source bucket and `s3:PutObject` points to the destination bucket.

---

## Error: `AccessDenied` when writing to the destination bucket

**Cause:** The IAM role's `s3:PutObject` permission resource ARN uses the wrong bucket name.

**Fix:** Double-check the ARN in the inline policy. It must be `arn:aws:s3:::lambda-s3-dest-<ACCOUNT_ID>/*` (with `/*` to cover all objects).

---

## Lambda is triggering in an infinite loop

**Symptom:** CloudWatch shows continuous invocations with the same function name.

**Cause:** Lambda is writing to the source bucket (or writing to a key under `uploads/` in the destination bucket), triggering another invocation.

**Fix:**

1. Verify you're writing to the **destination** bucket, not the source
2. Verify the prefix filter only matches `uploads/`
3. Verify `DEST_BUCKET` environment variable is set correctly

```bash
aws lambda get-function-configuration \
  --function-name S3FileProcessor \
  --query 'Environment.Variables'
```

---

## Result file appears but contains an error

**Symptom:** The result JSON in the destination bucket contains a stack trace rather than your expected summary.

**Fix:** Check CloudWatch Logs for the full traceback. Common causes:

- `KeyError: "Records"` — you invoked the function with a manual payload that doesn't match the S3 event schema
- `UnicodeDecodeError` — the file is binary (not text) but the extension was `.txt` or `.csv`; the code tries to decode it as UTF-8

---

## S3 console shows the event notification, but the function still isn't invoked

**Cause:** There is a propagation delay of up to 60 seconds when configuring a new S3 event notification. After saving the notification configuration, wait 60 seconds before uploading the first test file.

---

## `s3api delete-bucket` fails: "BucketNotEmpty"

**Fix:** Empty the bucket first:

```bash
aws s3 rm "s3://${BUCKET_NAME}" --recursive
# If versioning is enabled:
aws s3api list-object-versions \
  --bucket "$BUCKET_NAME" --output json \
  --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
  > /tmp/versions.json
# Then delete each version (see cleanup step for the script)
```
