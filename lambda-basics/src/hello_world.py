"""
Lambda Basics - Project 1
Hello World Lambda function.

The handler is the entry point AWS invokes. It always receives two arguments:
  event   - a dict containing the input data (varies by trigger source)
  context - a LambdaContext object with runtime metadata
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Event received: %s", json.dumps(event))

    logger.info("Function name      : %s", context.function_name)
    logger.info("Function version   : %s", context.function_version)
    logger.info("Invocation ID      : %s", context.aws_request_id)
    logger.info("Memory limit (MB)  : %s", context.memory_limit_in_mb)
    logger.info("Remaining time (ms): %s", context.get_remaining_time_in_millis())

    name = event.get("name", "World")
    message = f"Hello, {name}! This is your first Lambda function."

    return {
        "statusCode": 200,
        "body": json.dumps({"message": message}),
    }
