import json
import os
import boto3

sns_client = boto3.client("sns")

# Business events topic — downstream systems (fulfillment, inventory, etc.)
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

# Operational alerts topic — success/failure visibility for operators and monitoring.
# Optional: if not set, alerts are skipped and only CloudWatch logs are written.
ALERT_SNS_TOPIC_ARN = os.environ.get("ALERT_SNS_TOPIC_ARN")


def _publish_alert(status: str, subject: str, payload: dict) -> None:
    """Publish a success or failure alert to the ops alert topic.
    status must be 'SUCCESS' or 'FAILED' — used as an SNS filter attribute.
    """
    if not ALERT_SNS_TOPIC_ARN:
        return
    sns_client.publish(
        TopicArn=ALERT_SNS_TOPIC_ARN,
        Subject=subject,
        Message=json.dumps(payload),
        MessageAttributes={
            "status": {
                "DataType": "String",
                "StringValue": status,
            }
        },
    )


def lambda_handler(event, context):
    """
    Triggered by SQS. Processes each record and publishes results to SNS.

    On success: publishes the processed order to OrderNotifications (business topic)
                and an alert to OrderAlerts (ops topic) with status=SUCCESS.
    On failure: returns the message ID in batchItemFailures so SQS retries it,
                and publishes an alert to OrderAlerts with status=FAILED.
    """
    processed = []
    failed = []

    for record in event["Records"]:
        message_id = record["messageId"]
        try:
            body = json.loads(record["body"])
            order_id = body.get("orderId", "UNKNOWN")
            customer = body.get("customer", "Unknown Customer")
            amount = body.get("amount", 0)

            notification = {
                "orderId": order_id,
                "customer": customer,
                "amount": amount,
                "status": "PROCESSED",
                "message": f"Order {order_id} for {customer} (${amount}) has been processed.",
            }

            # Publish to business downstream topic
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"Order Processed: {order_id}",
                Message=json.dumps(notification),
                MessageAttributes={
                    "eventType": {
                        "DataType": "String",
                        "StringValue": "ORDER_PROCESSED",
                    }
                },
            )

            # Publish success alert to ops topic
            _publish_alert(
                status="SUCCESS",
                subject=f"SUCCESS: Order {order_id} processed",
                payload={
                    "status": "SUCCESS",
                    "orderId": order_id,
                    "customer": customer,
                    "amount": amount,
                    "sqsMessageId": message_id,
                },
            )

            print(f"Published SNS notification for order {order_id}")
            processed.append(message_id)

        except Exception as e:
            print(f"Failed to process message {message_id}: {e}")

            # Publish failure alert to ops topic before returning batchItemFailures
            _publish_alert(
                status="FAILED",
                subject=f"FAILED: Message processing error ({message_id})",
                payload={
                    "status": "FAILED",
                    "sqsMessageId": message_id,
                    "error": str(e),
                    # Include raw body so operators can inspect what was received
                    "rawBody": record.get("body", ""),
                },
            )

            # Returning a batchItemFailures response tells SQS to retry only
            # the failed messages rather than the entire batch.
            failed.append({"itemIdentifier": message_id})

    print(f"Processed: {len(processed)}, Failed: {len(failed)}")

    if failed:
        return {"batchItemFailures": failed}

    return {"statusCode": 200, "body": f"Processed {len(processed)} message(s)"}
