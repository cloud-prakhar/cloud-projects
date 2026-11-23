"""bookstore-orders Lambda — the orders slice of the strangled monolith.

Handles the write/order routes:
    POST /orders        -> create order
    GET  /orders/{id}   -> one order

Backed by the DynamoDB 'Orders' table. It validates the book exists by reading
the 'Books' table (catalog), which is why its role gets read access to Books too.
"""

import base64
import json
import os
from decimal import Decimal
import uuid

import boto3

ORDERS_TABLE = os.environ.get("ORDERS_TABLE", "Orders")
BOOKS_TABLE = os.environ.get("BOOKS_TABLE", "Books")
APP_VERSION = os.environ.get("APP_VERSION", "orders-1.0")

_ddb = boto3.resource("dynamodb")
_orders = _ddb.Table(ORDERS_TABLE)
_books = _ddb.Table(BOOKS_TABLE)


def _json_default(value):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    return str(value)


def _resp(status, body):
    return {"statusCode": status, "headers": {"content-type": "application/json"},
            "body": json.dumps(body, default=_json_default)}


def _parse_body(event):
    raw = event.get("body") or "{}"
    # HTTP API base64-encodes bodies whose content-type isn't JSON/text (e.g. curl -d
    # without -H 'content-type: application/json'); the monolith accepted those.
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        body = json.loads(raw)
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def handler(event, context):
    method = event["requestContext"]["http"]["method"]
    order_id = (event.get("pathParameters") or {}).get("id")

    if method == "GET" and order_id:
        item = _orders.get_item(Key={"id": order_id}).get("Item")
        return _resp(200, item) if item else _resp(404, {"error": "not found"})

    if method == "POST":
        body = _parse_body(event)
        if body is None:
            return _resp(400, {"error": "body must be JSON"})
        if not _books.get_item(Key={"id": body.get("book_id", "")}).get("Item"):
            return _resp(400, {"error": "unknown book_id"})
        new_id = str(uuid.uuid4())
        _orders.put_item(Item={
            "id": new_id, "book_id": body["book_id"],
            "qty": int(body.get("qty", 1)), "status": "PLACED",
            "version": APP_VERSION,
        })
        return _resp(201, {"id": new_id, "status": "PLACED"})

    return _resp(405, {"error": f"{method} not supported"})
