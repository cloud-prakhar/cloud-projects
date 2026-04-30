"""
Lambda Layers — Project 3
Lambda function that uses the 'requests' library provided by a Lambda layer.

This function would fail without the RequestsLayer attached because 'requests'
is not part of the Python 3.14 standard library or Lambda's built-in runtime.

The layer installs 'requests' under /opt/python/lib/python3.14/site-packages/,
which the runtime automatically adds to sys.path at startup.
"""

import json
import logging

import requests  # provided by RequestsLayer

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PUBLIC_API = "https://httpbin.org/get"


def handler(event, context):
    url = event.get("url", PUBLIC_API)
    logger.info("Fetching URL: %s", url)

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    logger.info("Response status: %d", response.status_code)
    logger.info("Headers sent   : %s", json.dumps(dict(response.request.headers)))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "fetched_url": url,
            "http_status": response.status_code,
            "response_preview": str(data)[:500],
        }),
    }
