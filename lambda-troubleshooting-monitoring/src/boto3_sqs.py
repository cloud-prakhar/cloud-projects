"""
Lambda Troubleshooting & Monitoring — Project 4
Boto3 automation: SQS operations from Lambda.

Demonstrates SQS management tasks: sending messages, reading queue
attributes, purging queues, and managing dead-letter queues.

IAM permissions required:
  sqs:SendMessage
  sqs:ReceiveMessage
  sqs:DeleteMessage
  sqs:GetQueueAttributes
  sqs:GetQueueUrl
  sqs:PurgeQueue

Invoke with:
  {"action": "send",   "queue_name": "MyQueue", "message": "hello", "delay": 0}
  {"action": "stats",  "queue_name": "MyQueue"}
  {"action": "peek",   "queue_name": "MyQueue", "max_messages": 5}
  {"action": "purge",  "queue_name": "MyQueue"}
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
sqs = boto3.client("sqs", region_name=REGION)


def handler(event, context):
    action = event.get("action", "stats")
    logger.info("SQS action: %s | request_id: %s", action, context.aws_request_id)

    dispatch = {
        "send":  _send_message,
        "stats": _queue_stats,
        "peek":  _peek_messages,
        "purge": _purge_queue,
    }

    fn = dispatch.get(action)
    if fn is None:
        return {"statusCode": 400, "body": f"Unknown action: {action}"}

    try:
        return fn(event)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        logger.error("SQS ClientError: %s — %s", code, msg)
        return {"statusCode": 500, "body": json.dumps({"error": code, "message": msg})}


def _get_queue_url(queue_name: str) -> str:
    response = sqs.get_queue_url(QueueName=queue_name)
    return response["QueueUrl"]


def _send_message(event: dict) -> dict:
    queue_name = event["queue_name"]
    message    = event.get("message", "test message from Lambda")
    delay      = int(event.get("delay", 0))
    attributes = event.get("attributes", {})

    queue_url = _get_queue_url(queue_name)

    msg_attrs = {
        k: {"DataType": "String", "StringValue": str(v)}
        for k, v in attributes.items()
    }

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=message if isinstance(message, str) else json.dumps(message),
        DelaySeconds=delay,
        MessageAttributes=msg_attrs,
    )

    message_id = response["MessageId"]
    logger.info("Sent message %s to %s", message_id, queue_name)
    return {"statusCode": 200, "body": json.dumps({"message_id": message_id, "queue": queue_name})}


def _queue_stats(event: dict) -> dict:
    queue_name = event["queue_name"]
    queue_url = _get_queue_url(queue_name)

    attrs = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=[
            "ApproximateNumberOfMessages",
            "ApproximateNumberOfMessagesNotVisible",
            "ApproximateNumberOfMessagesDelayed",
            "CreatedTimestamp",
            "VisibilityTimeout",
            "MessageRetentionPeriod",
            "RedrivePolicy",
        ],
    )["Attributes"]

    stats = {
        "queue_name":          queue_name,
        "messages_available":  int(attrs.get("ApproximateNumberOfMessages", 0)),
        "messages_in_flight":  int(attrs.get("ApproximateNumberOfMessagesNotVisible", 0)),
        "messages_delayed":    int(attrs.get("ApproximateNumberOfMessagesDelayed", 0)),
        "visibility_timeout_s": int(attrs.get("VisibilityTimeout", 0)),
        "retention_period_s":  int(attrs.get("MessageRetentionPeriod", 0)),
        "has_dlq":             "RedrivePolicy" in attrs,
    }

    logger.info("Queue stats for %s: %s", queue_name, json.dumps(stats))
    return {"statusCode": 200, "body": json.dumps(stats)}


def _peek_messages(event: dict) -> dict:
    queue_name   = event["queue_name"]
    max_messages = min(int(event.get("max_messages", 5)), 10)
    queue_url    = _get_queue_url(queue_name)

    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=1,
        AttributeNames=["All"],
        MessageAttributeNames=["All"],
    )

    messages = []
    for msg in response.get("Messages", []):
        messages.append({
            "message_id":      msg["MessageId"],
            "body":            msg["Body"],
            "received_at":     msg.get("Attributes", {}).get("ApproximateFirstReceiveTimestamp"),
            "receive_count":   msg.get("Attributes", {}).get("ApproximateReceiveCount"),
        })

    logger.info("Peeked %d messages from %s (not deleted — still visible after timeout)", len(messages), queue_name)
    return {"statusCode": 200, "body": json.dumps({"messages": messages, "count": len(messages)})}


def _purge_queue(event: dict) -> dict:
    queue_name = event["queue_name"]
    queue_url = _get_queue_url(queue_name)

    sqs.purge_queue(QueueUrl=queue_url)
    logger.info("Purged queue: %s — all messages deleted", queue_name)
    return {"statusCode": 200, "body": json.dumps({"purged": queue_name})}
