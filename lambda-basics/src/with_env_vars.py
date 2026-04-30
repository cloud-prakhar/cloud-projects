"""
Lambda Basics - Project 1
Demonstrates reading environment variables inside a Lambda function.

Environment variables are ideal for:
  - Stage flags     (ENV=prod / ENV=dev)
  - Feature toggles (FEATURE_X_ENABLED=true)
  - External endpoints / ARNs that differ between environments
  - Secrets Manager / SSM Parameter paths (NOT raw secrets)

Never hard-code region names, account IDs, ARNs, or credentials in code.
"""

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Read once at cold-start; reused across warm invocations.
APP_ENV = os.environ.get("APP_ENV", "dev")
TABLE_NAME = os.environ.get("TABLE_NAME", "")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))


def handler(event, context):
    logger.info("Running in environment: %s", APP_ENV)

    if not TABLE_NAME:
        # Fail loudly at runtime so a misconfigured deploy is caught immediately.
        raise EnvironmentError("TABLE_NAME environment variable is not set.")

    config = {
        "environment": APP_ENV,
        "table_name": TABLE_NAME,
        "max_retries": MAX_RETRIES,
    }

    logger.info("Config snapshot: %s", json.dumps(config))

    return {
        "statusCode": 200,
        "body": json.dumps(config),
    }
