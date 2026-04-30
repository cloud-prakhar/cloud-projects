# Step 5 — Testing the End-to-End Pipeline

---

## 5.1 Upload a Text File via the Console

1. Open **S3 → lambda-s3-source-YOUR_ACCOUNT_ID**.
2. Click **Create folder**, name it `uploads`, click **Create folder**.
3. Click into the `uploads/` folder.
4. Click **Upload** → **Add files** → select any `.txt` file from your computer.
5. Click **Upload**.

After the upload completes, wait about 10–15 seconds, then:

1. Open **S3 → lambda-s3-dest-YOUR_ACCOUNT_ID**.
2. Navigate to `results/uploads/`.
3. You should see a `.json` file named after your uploaded file.
4. Click the file → **Open** to view the summary.

> **If the result does not appear within 60 seconds**, the S3 event trigger may be restricted by your account's permissions. Use the manual invocation method in Step 3 instead — the code is identical. See [troubleshooting.md](../troubleshooting.md) for details.

---

## 5.2 Upload a CSV File

1. Create a file named `orders.csv` on your computer with this content:

   ```
   order_id,customer,product,quantity,price
   1001,Alice,Widget,2,9.99
   1002,Bob,Gadget,1,49.99
   1003,Charlie,Doohickey,5,4.99
   ```

2. Upload it to `uploads/` in the source bucket (same steps as 5.1).

3. Check the destination bucket for `results/uploads/orders.csv.json`. It should contain:

   ```json
   {
     "extension": "csv",
     "summary": {
       "type": "csv",
       "row_count": 3,
       "column_count": 5,
       "headers": ["order_id", "customer", "product", "quantity", "price"]
     }
   }
   ```

---

## 5.3 Test with CLI (Fastest Method)

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SOURCE_BUCKET="lambda-s3-source-${ACCOUNT_ID}"
DEST_BUCKET="lambda-s3-dest-${ACCOUNT_ID}"

# Upload text file
echo -e "Hello Lambda!\nLine two.\nLine three." \
  | aws s3 cp - "s3://${SOURCE_BUCKET}/uploads/cli-test.txt"

# Wait for processing
sleep 15

# Check result
aws s3 cp "s3://${DEST_BUCKET}/results/uploads/cli-test.txt.json" - | python3 -m json.tool
```

---

## 5.4 Automated Test Script

```bash
cd /path/to/lambda-s3-event-processing
pip install boto3

export SOURCE_BUCKET="lambda-s3-source-${ACCOUNT_ID}"
export DEST_BUCKET="lambda-s3-dest-${ACCOUNT_ID}"

python src/test_upload.py
```

The script uploads a text file, CSV, and binary file, then polls for each result.

---

## 5.5 Test File with Spaces in the Name

```bash
echo "Test content" \
  | aws s3 cp - "s3://${SOURCE_BUCKET}/uploads/my file name.txt"
sleep 15
aws s3 cp "s3://${DEST_BUCKET}/results/uploads/my file name.txt.json" - 2>&1
```

S3 encodes the space as `+` in the event payload key. The handler uses `urllib.parse.unquote_plus()` to decode it back. Verify the result key name has the actual space, not `+` or `%20`.

---

## 5.6 Test Prefix Filter — File Outside `uploads/` Should NOT Trigger Lambda

```bash
echo "Should not trigger Lambda" \
  | aws s3 cp - "s3://${SOURCE_BUCKET}/other/ignored.txt"
```

Wait 30 seconds and check CloudWatch Logs — no new invocation should appear for this upload.

---

## 5.7 Verify Logs in CloudWatch

1. Open **Lambda → S3FileProcessor → Monitor → View CloudWatch logs**.
2. Click the most recent log stream.
3. You should see lines like:

   ```
   Processing s3://lambda-s3-source-.../uploads/cli-test.txt (35 bytes)
   Result written to s3://lambda-s3-dest-.../results/uploads/cli-test.txt.json
   ```

---

## Checkpoint

- [ ] Uploaded at least one `.txt` and one `.csv` file; both produced result JSON files
- [ ] File with spaces in the name processed correctly (decoded key)
- [ ] File uploaded outside `uploads/` did NOT trigger Lambda
- [ ] CloudWatch shows the processing log lines for each invocation

---

**Next:** [Step 6 — Cleanup](./06-cleanup.md)
