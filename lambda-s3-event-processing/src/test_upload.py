"""
Lambda S3 Event Processing — Project 2
Test script: uploads sample files to the source bucket and waits for
the result file to appear in the destination bucket.

Usage:
    python src/test_upload.py

Set SOURCE_BUCKET and DEST_BUCKET before running:
    export SOURCE_BUCKET=lambda-s3-source-<your-account-id>
    export DEST_BUCKET=lambda-s3-dest-<your-account-id>
"""

import json
import os
import time

import boto3

SOURCE_BUCKET = os.environ["SOURCE_BUCKET"]
DEST_BUCKET = os.environ["DEST_BUCKET"]
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

s3 = boto3.client("s3", region_name=REGION)

SAMPLES = {
    "uploads/sample.txt": (
        "The quick brown fox jumps over the lazy dog.\n"
        "Lambda is a serverless compute service.\n"
        "S3 stores objects durably across multiple AZs.\n"
    ),
    "uploads/orders.csv": (
        "order_id,customer,product,quantity,price\n"
        "1001,Alice,Widget,2,9.99\n"
        "1002,Bob,Gadget,1,49.99\n"
        "1003,Charlie,Doohickey,5,4.99\n"
    ),
    "uploads/data.bin": b"\x00\x01\x02\x03\x04\xff\xfe",
}


def upload_file(key: str, content) -> None:
    if isinstance(content, str):
        content = content.encode()
    s3.put_object(Bucket=SOURCE_BUCKET, Key=key, Body=content)
    print(f"  Uploaded: s3://{SOURCE_BUCKET}/{key}")


def wait_for_result(source_key: str, timeout: int = 30) -> dict | None:
    dest_key = f"results/{source_key}.json"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            obj = s3.get_object(Bucket=DEST_BUCKET, Key=dest_key)
            return json.loads(obj["Body"].read())
        except s3.exceptions.NoSuchKey:
            time.sleep(2)
    return None


if __name__ == "__main__":
    print(f"\nSource bucket : {SOURCE_BUCKET}")
    print(f"Dest bucket   : {DEST_BUCKET}\n")

    for key, content in SAMPLES.items():
        print(f"\n--- Uploading {key} ---")
        upload_file(key, content)

        print(f"  Waiting for Lambda to process...")
        result = wait_for_result(key)
        if result:
            print(f"  Result: {json.dumps(result, indent=4)}")
        else:
            print(f"  [TIMEOUT] No result found after 30 seconds — check CloudWatch Logs")
