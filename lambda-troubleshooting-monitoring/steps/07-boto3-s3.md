# Step 7 — S3 Automation with Lambda and Boto3

Deploy the S3 automation function. Common uses:
- **Pre-signed URLs** — give users temporary download access without exposing credentials
- **Cross-bucket copy** — move objects as part of an archive pipeline
- **Inventory** — list objects in a prefix for auditing

---

## 7.1 Package and Create the Function

```bash
zip -j s3_automation.zip src/boto3_s3.py
```

1. **Lambda → Create function → Author from scratch**

   | Field | Value |
   |-------|-------|
   | Function name | `S3AutomationFn` |
   | Runtime | **Python 3.14** |
   | Execution role | `LambdaTroubleshootingRole` |

2. Upload `s3_automation.zip` → Handler: `boto3_s3.handler` → Timeout: 30 sec.

---

## 7.2 Test: List All S3 Buckets

1. **Test** tab → Event name: `ListBuckets`
2. Paste:
   ```json
   { "action": "list_buckets" }
   ```
3. Click **Test**.

Expected: a list of all buckets in your account. You'll see at least `lambda-s3-source-*` and `lambda-s3-dest-*` from Project 2.

---

## 7.3 Test: List Objects in a Bucket

1. Event name: `ListObjects`
2. Paste (replace with a real bucket):
   ```json
   {
     "action": "list_objects",
     "bucket": "lambda-s3-source-YOUR_ACCOUNT_ID",
     "prefix": "uploads/",
     "max_keys": 10
   }
   ```
3. Click **Test**.

---

## 7.4 Test: Generate a Pre-Signed URL

Pre-signed URLs give a user temporary access to a private S3 object without requiring AWS credentials.

1. First, confirm a file exists:
   ```bash
   aws s3 ls s3://lambda-s3-source-YOUR_ACCOUNT_ID/uploads/
   ```

2. Event name: `PresignURL`
3. Paste:
   ```json
   {
     "action": "presign",
     "bucket": "lambda-s3-source-YOUR_ACCOUNT_ID",
     "key": "uploads/test-manual.txt",
     "expires": 3600
   }
   ```
4. Click **Test**.

The response contains a long URL with a signature. Open it in your browser — the file downloads without any AWS authentication. The URL expires in 3600 seconds (1 hour).

---

## 7.5 Error Handling Pattern

Notice that `boto3_s3.handler` wraps all calls in `try/except ClientError`:

```python
except ClientError as e:
    code = e.response["Error"]["Code"]   # e.g. "NoSuchKey", "AccessDenied"
    msg  = e.response["Error"]["Message"]
    logger.error("S3 ClientError: %s — %s", code, msg)
    return {"statusCode": 500, "body": json.dumps({"error": code, "message": msg})}
```

This returns a structured error response rather than an unhandled exception traceback — better for callers and easier to parse in CloudWatch Log Insights.

---

## Checkpoint

- [ ] `S3AutomationFn` deployed and Active
- [ ] List buckets returned your account's buckets
- [ ] Generated a pre-signed URL and opened it in a browser

---

**Next:** [Step 8 — SQS Automation](./08-boto3-sqs.md)
