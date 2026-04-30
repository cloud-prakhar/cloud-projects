"""
Lambda Basics - Project 1
Local test script to invoke your Lambda function via Boto3.

Usage:
    python src/test_invoke.py

Prerequisites:
    pip install boto3
    AWS credentials configured (aws configure or env vars)
"""

import json
import boto3

FUNCTION_NAME = "HelloWorldLambda"
REGION = "us-east-1"

client = boto3.client("lambda", region_name=REGION)

test_payloads = [
    {"name": "Alice"},
    {"name": "Bob"},
    {},  # triggers the default "World" fallback
]


def invoke(payload: dict) -> dict:
    response = client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode(),
    )
    status = response["StatusCode"]
    body = json.loads(response["Payload"].read())
    return {"http_status": status, "response": body}


if __name__ == "__main__":
    for payload in test_payloads:
        print(f"\nInvoking with payload: {payload}")
        result = invoke(payload)
        print(f"  HTTP status : {result['http_status']}")
        print(f"  Response    : {json.dumps(result['response'], indent=2)}")
