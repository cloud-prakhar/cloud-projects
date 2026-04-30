# Challenges — Lambda S3 Event Processing

---

## Challenge 1 — Add JSON File Support

Extend `s3_processor.py` to handle `.json` files. For each JSON file, output the top-level key names and the count of keys:

```json
{
  "type": "json",
  "key_count": 5,
  "keys": ["id", "name", "email", "created_at", "active"]
}
```

Handle malformed JSON by catching `json.JSONDecodeError` and returning `{"type": "json", "error": "invalid_json"}`.

---

## Challenge 2 — S3 Object Tagging

After processing a file, add a tag to the **source object** indicating it was processed:

```python
s3.put_object_tagging(
    Bucket=bucket,
    Key=key,
    Tagging={"TagSet": [{"Key": "processed", "Value": "true"}]}
)
```

You'll need to add `s3:PutObjectTagging` permission to the IAM role.

Use the Console or CLI to verify the tag appears on the uploaded object.

---

## Challenge 3 — File Size Limit

Add a guard at the start of `_process_record()`:

- If `record["s3"]["object"]["size"] > 10_000_000` (10 MB), skip processing and write a result JSON with `{"error": "file_too_large", "size_bytes": <actual_size>}` to the destination.
- Log a warning when this happens.

Upload a file larger than 10 MB to verify the guard triggers. (Generate one with `dd if=/dev/urandom of=bigfile.bin bs=1M count=11`.)

---

## Challenge 4 — SNS Notification on Completion

Send an SNS notification every time a file is successfully processed. Include the source key, extension, and summary in the message.

Steps:
1. Create an SNS topic and subscribe your email
2. Add `sns:Publish` to the IAM role (scoped to the topic ARN)
3. Add `SNS_TOPIC_ARN` as an environment variable
4. Call `boto3.client("sns").publish()` at the end of `_process_record()`

---

## Challenge 5 — Idempotency via DynamoDB

Lambda with async triggers can be invoked more than once for the same event (S3 guarantees at-least-once delivery). Make the function **idempotent**:

1. Create a DynamoDB table `ProcessedFiles` with `source_key` as the partition key
2. At the start of `_process_record()`, attempt a `conditional_write` that fails if the key already exists
3. If it fails (`ConditionalCheckFailedException`), log "already processed" and return early

This ensures that even if S3 delivers the event twice, the file is only processed once.
