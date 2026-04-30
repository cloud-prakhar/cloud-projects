# Lambda with S3 Event Processing

## What You'll Build

An **event-driven file processing pipeline**: every time a file is uploaded to an S3 source bucket, Lambda is automatically triggered, processes the file (word count for `.txt`, row/column stats for `.csv`), and writes a JSON result to a separate destination bucket.

This pattern is foundational in data engineering, media processing, ETL, and log aggregation.

---

## Architecture

```
  You (Console / CLI / SDK)
           │
           │ s3:PutObject
           ▼
  ┌──────────────────────┐
  │   S3 Source Bucket   │
  │  lambda-s3-source-*  │
  │  prefix: uploads/    │
  └──────────┬───────────┘
             │  S3 Event Notification
             │  (s3:ObjectCreated:*)
             ▼
  ┌──────────────────────┐
  │   Lambda Function    │
  │   "S3FileProcessor"  │
  │   Python 3.14        │
  │                      │
  │  - Reads the file    │
  │  - Analyses content  │
  │  - Writes result JSON│
  └──────────┬───────────┘
             │ s3:PutObject
             ▼
  ┌──────────────────────┐
  │   S3 Dest Bucket     │
  │  lambda-s3-dest-*    │
  │  prefix: results/    │
  └──────────────────────┘
             │
             ▼
  ┌──────────────────────┐
  │  CloudWatch Logs     │
  │ /aws/lambda/S3File.. │
  └──────────────────────┘
```

**Key concepts:**
- **S3 Event Notification:** S3 calls Lambda when an object is created. The event payload identifies the bucket and key.
- **Two buckets:** Source and destination are separate. If the trigger bucket and write bucket were the same, a processing result could retrigger Lambda infinitely.
- **URL-encoded key names:** S3 event payloads encode the object key (spaces → `+`, special chars → `%XX`). The function uses `urllib.parse.unquote_plus()` to decode them.
- **IAM least privilege:** The execution role has `s3:GetObject` on the source bucket and `s3:PutObject` on the destination bucket — nothing broader.

---

## Project Structure

```
lambda-s3-event-processing/
├── README.md
├── steps/
│   ├── 01-iam-role.md          ← Role with S3 read/write permissions
│   ├── 02-s3-buckets.md        ← Create source and destination buckets
│   ├── 03-lambda-function.md   ← Deploy the processor function
│   ├── 04-s3-trigger.md        ← Wire the S3 event notification
│   ├── 05-testing.md           ← Upload files and verify results
│   └── 06-cleanup.md
├── src/
│   ├── s3_processor.py         ← Lambda handler
│   └── test_upload.py          ← Boto3 test script
├── troubleshooting.md
└── challenges.md
```

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| AWS account | Console access — Lambda, S3, IAM, CloudWatch |
| AWS CLI | v2.x |
| Python | 3.9+ locally |
| Boto3 | `pip install boto3` |
| Completed | [Lambda Basics](../lambda-basics/README.md) — you should understand handlers and IAM roles |

---

## What the S3 Event Payload Looks Like

When you upload a file, Lambda receives:

```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "lambda-s3-source-123456789012"
        },
        "object": {
          "key": "uploads/sample.txt",
          "size": 145
        }
      }
    }
  ]
}
```

Your handler iterates `event["Records"]` because S3 can batch multiple events (though for `ObjectCreated` events, batches are typically size 1).

---

## Step by Step

| Step | File | Goal |
|------|------|------|
| 1 | `01-iam-role.md` | Create a role with S3 read + write permissions |
| 2 | `02-s3-buckets.md` | Create source and destination buckets |
| 3 | `03-lambda-function.md` | Deploy the file processor |
| 4 | `04-s3-trigger.md` | Configure S3 to trigger Lambda on uploads |
| 5 | `05-testing.md` | Upload test files and verify results |
| 6 | `06-cleanup.md` | Delete all resources |

Start with **Step 1 →** [`steps/01-iam-role.md`](steps/01-iam-role.md)

---

## Estimated Time

60 – 90 minutes.

## Estimated Cost

Free Tier covers all activity in this project. S3 standard storage and Lambda invocations are within free limits for testing volumes.

---

## What's Next

- [Lambda Layers](../lambda-layers/README.md) — package third-party dependencies for reuse
- [Lambda Troubleshooting & Monitoring](../lambda-troubleshooting-monitoring/README.md) — CloudWatch Logs, X-Ray, DLQs
