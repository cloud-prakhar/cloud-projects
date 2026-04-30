"""
Lambda Troubleshooting & Monitoring — Project 4
Boto3 automation: S3 operations from Lambda.

Demonstrates S3 automation tasks: listing buckets/objects, generating
pre-signed URLs, copying objects, and applying lifecycle policies.

IAM permissions required:
  s3:ListAllMyBuckets
  s3:ListBucket       (on specific buckets)
  s3:GetObject
  s3:CopyObject
  s3:PutLifecycleConfiguration

Invoke with:
  {"action": "list_buckets"}
  {"action": "list_objects", "bucket": "my-bucket", "prefix": "uploads/"}
  {"action": "presign",      "bucket": "my-bucket", "key": "uploads/file.txt", "expires": 3600}
  {"action": "copy",         "src_bucket": "a", "src_key": "k", "dst_bucket": "b", "dst_key": "k"}
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
s3_client = boto3.client("s3", region_name=REGION)
s3_resource = boto3.resource("s3", region_name=REGION)


def handler(event, context):
    action = event.get("action", "list_buckets")
    logger.info("S3 action: %s | request_id: %s", action, context.aws_request_id)

    dispatch = {
        "list_buckets":  _list_buckets,
        "list_objects":  _list_objects,
        "presign":       _presign_url,
        "copy":          _copy_object,
    }

    fn = dispatch.get(action)
    if fn is None:
        return {"statusCode": 400, "body": f"Unknown action: {action}"}

    try:
        return fn(event)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        logger.error("S3 ClientError: %s — %s", code, msg)
        return {"statusCode": 500, "body": json.dumps({"error": code, "message": msg})}


def _list_buckets(event: dict) -> dict:
    response = s3_client.list_buckets()
    buckets = [
        {"name": b["Name"], "created": b["CreationDate"].isoformat()}
        for b in response.get("Buckets", [])
    ]
    logger.info("Found %d buckets", len(buckets))
    return {"statusCode": 200, "body": json.dumps({"buckets": buckets})}


def _list_objects(event: dict) -> dict:
    bucket = event["bucket"]
    prefix = event.get("prefix", "")
    max_keys = int(event.get("max_keys", 20))

    paginator = s3_client.get_paginator("list_objects_v2")
    objects = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, PaginationConfig={"MaxItems": max_keys}):
        for obj in page.get("Contents", []):
            objects.append({
                "key":           obj["Key"],
                "size_bytes":    obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })

    logger.info("Listed %d objects in s3://%s/%s", len(objects), bucket, prefix)
    return {"statusCode": 200, "body": json.dumps({"objects": objects, "count": len(objects)})}


def _presign_url(event: dict) -> dict:
    bucket = event["bucket"]
    key = event["key"]
    expires = int(event.get("expires", 3600))

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )

    logger.info("Generated pre-signed URL for s3://%s/%s (expires %ds)", bucket, key, expires)
    return {
        "statusCode": 200,
        "body": json.dumps({"url": url, "expires_in_seconds": expires}),
    }


def _copy_object(event: dict) -> dict:
    src_bucket = event["src_bucket"]
    src_key    = event["src_key"]
    dst_bucket = event["dst_bucket"]
    dst_key    = event["dst_key"]

    s3_client.copy_object(
        CopySource={"Bucket": src_bucket, "Key": src_key},
        Bucket=dst_bucket,
        Key=dst_key,
    )
    logger.info(
        "Copied s3://%s/%s → s3://%s/%s",
        src_bucket, src_key, dst_bucket, dst_key,
    )
    return {
        "statusCode": 200,
        "body": json.dumps({
            "source":      f"s3://{src_bucket}/{src_key}",
            "destination": f"s3://{dst_bucket}/{dst_key}",
        }),
    }
