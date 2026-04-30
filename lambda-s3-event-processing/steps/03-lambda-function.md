# Step 3 — Deploy the S3 File Processor Lambda

In this step you package and deploy `src/s3_processor.py` and set the required `DEST_BUCKET` environment variable.

---

## 3.1 Review the Handler

Open `src/s3_processor.py`. Key things to notice before deploying:

1. **`boto3.client("s3")`** is created at module level (outside the handler). Reusing the client across warm invocations avoids repeated TLS handshakes.
2. **`urllib.parse.unquote_plus(key)`** — S3 encodes spaces in key names as `+` in event payloads. Forgetting this causes `NoSuchKey` errors when file names contain spaces.
3. **`event["Records"]`** — S3 events always wrap notifications in a list. Your handler iterates the list to handle batched events.

---

## 3.2 Package the Code

```bash
cd /path/to/lambda-s3-event-processing

# -j strips directory prefixes so s3_processor.py lands at ZIP root
zip -j s3_processor.zip src/s3_processor.py
```

---

## 3.3 Create the Function in the Console

1. In the AWS Console, open **Lambda** → **Create function**.
2. Select **Author from scratch**.

   | Field | Value |
   |-------|-------|
   | Function name | `S3FileProcessor` |
   | Runtime | **Python 3.14** |
   | Architecture | x86_64 |

3. Under **Permissions → Change default execution role**:

   | Field | Value |
   |-------|-------|
   | Execution role | **Use an existing role** |
   | Existing role | `LambdaS3ProcessorRole` |

4. Click **Create function**.

---

## 3.4 Upload the Code

1. On the function page → **Code source** → **Upload from** → **.zip file**.
2. Select `s3_processor.zip`.
3. Click **Save**.

Update the handler string:

1. **Configuration** tab → **General configuration** → **Edit**.
2. Set **Handler** to `s3_processor.handler`.
3. Set **Memory** to `256 MB` and **Timeout** to `30 sec`.
4. Click **Save**.

---

## 3.5 Set the Environment Variable

1. **Configuration** tab → **Environment variables** → **Edit**.
2. Click **Add environment variable**:

   | Key | Value |
   |-----|-------|
   | `DEST_BUCKET` | `lambda-s3-dest-YOUR_ACCOUNT_ID` |

3. Click **Save**.

---

## 3.6 Test with a Manual Invocation (Before Wiring the Trigger)

First upload a test file to the source bucket:

```bash
echo "Hello Lambda from S3!" \
  | aws s3 cp - "s3://lambda-s3-source-YOUR_ACCOUNT_ID/uploads/test-manual.txt"
```

Create a test event in the Console:

1. Click the **Test** tab → **Create new event**.
2. Event name: `ManualS3Event`
3. Paste:

```json
{
  "Records": [{
    "s3": {
      "bucket": { "name": "lambda-s3-source-YOUR_ACCOUNT_ID" },
      "object": { "key": "uploads/test-manual.txt", "size": 22 }
    }
  }]
}
```

4. Click **Save**, then **Test**.

Expected response:

```json
{
  "statusCode": 200,
  "processed": 1,
  "results": [{
    "extension": "txt",
    "summary": { "type": "text", "line_count": 1, "word_count": 4, "char_count": 22 }
  }]
}
```

Check the result file in the destination bucket:

```bash
aws s3 cp \
  "s3://lambda-s3-dest-YOUR_ACCOUNT_ID/results/uploads/test-manual.txt.json" -
```

---

## AWS CLI (Deploy Alternatively)

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/LambdaS3ProcessorRole"

zip -j s3_processor.zip src/s3_processor.py

aws lambda create-function \
  --function-name S3FileProcessor \
  --runtime python3.14 \
  --role "$ROLE_ARN" \
  --handler s3_processor.handler \
  --zip-file fileb://s3_processor.zip \
  --timeout 30 --memory-size 256 \
  --environment "Variables={DEST_BUCKET=lambda-s3-dest-${ACCOUNT_ID}}"

aws lambda wait function-active --function-name S3FileProcessor
```

---

## Checkpoint

- [ ] `S3FileProcessor` is Active with runtime Python 3.14
- [ ] Handler is `s3_processor.handler`
- [ ] `DEST_BUCKET` environment variable is set
- [ ] Manual invocation with a synthetic S3 event returned a JSON summary
- [ ] Result file appeared in the destination bucket

---

**Next:** [Step 4 — Configure the S3 Event Trigger](./04-s3-trigger.md)
