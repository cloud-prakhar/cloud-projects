"""
Lambda S3 Event Processing — Project 2
Triggered by S3 PutObject events. Reads the uploaded file, processes it,
and writes a result file to a separate destination bucket.

Supported file types:
  .txt  → word count summary
  .csv  → row/column count summary
  other → metadata echo
"""

import csv
import io
import json
import logging
import os
import urllib.parse

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
DEST_BUCKET = os.environ["DEST_BUCKET"]


def handler(event, context):
    logger.info("Event: %s", json.dumps(event))

    results = []
    for record in event["Records"]:
        result = _process_record(record)
        results.append(result)
        logger.info("Processed record: %s", json.dumps(result))

    return {"statusCode": 200, "processed": len(results), "results": results}


def _process_record(record: dict) -> dict:
    bucket = record["s3"]["bucket"]["name"]
    # S3 key names are URL-encoded in event payloads (spaces become +, etc.)
    key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
    size = record["s3"]["object"]["size"]

    logger.info("Processing s3://%s/%s (%d bytes)", bucket, key, size)

    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read().decode("utf-8")

    extension = key.rsplit(".", 1)[-1].lower() if "." in key else ""
    if extension == "txt":
        summary = _analyse_text(body)
    elif extension == "csv":
        summary = _analyse_csv(body)
    else:
        summary = {"type": "unknown", "size_bytes": size}

    result = {
        "source_bucket": bucket,
        "source_key": key,
        "extension": extension,
        "summary": summary,
    }

    dest_key = f"results/{key}.json"
    s3.put_object(
        Bucket=DEST_BUCKET,
        Key=dest_key,
        Body=json.dumps(result, indent=2),
        ContentType="application/json",
    )
    logger.info("Result written to s3://%s/%s", DEST_BUCKET, dest_key)

    return result


def _analyse_text(content: str) -> dict:
    lines = content.splitlines()
    words = content.split()
    return {
        "type": "text",
        "line_count": len(lines),
        "word_count": len(words),
        "char_count": len(content),
    }


def _analyse_csv(content: str) -> dict:
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return {"type": "csv", "row_count": 0, "column_count": 0}
    return {
        "type": "csv",
        "row_count": len(rows) - 1,  # exclude header
        "column_count": len(rows[0]),
        "headers": rows[0],
    }
