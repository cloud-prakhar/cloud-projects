"""Local validation for the catalog + orders handlers — no AWS required.

Fakes the DynamoDB tables in memory by monkeypatching boto3 before importing
the handlers, so you can prove the routing/logic on your laptop:

    cd src
    python3 test_handlers.py     # prints PASS/FAIL, no pytest needed
"""

import base64
import importlib.util
import json
import os
import sys
import types

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# ---- in-memory fake of boto3.resource("dynamodb").Table(...) ----
_TABLES = {"Books": {}, "Orders": {}}


class _FakeTable:
    def __init__(self, name):
        self.name = name

    def get_item(self, Key):
        item = _TABLES[self.name].get(Key["id"])
        return {"Item": item} if item else {}

    def put_item(self, Item):
        _TABLES[self.name][Item["id"]] = Item

    def scan(self):
        return {"Items": list(_TABLES[self.name].values())}


class _FakeResource:
    def Table(self, name):
        return _FakeTable(name)


fake_boto3 = types.ModuleType("boto3")
fake_boto3.resource = lambda *_a, **_k: _FakeResource()
sys.modules["boto3"] = fake_boto3


def _load(mod_name, rel_path):
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(here, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


catalog = _load("catalog_handler", "catalog/handler.py")
orders = _load("orders_handler", "orders/handler.py")

_PASS = 0
_FAIL = 0


def check(name, cond):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"PASS  {name}")
    else:
        _FAIL += 1
        print(f"FAIL  {name}")


def evt(method, path, path_params=None, body=None):
    return {
        "requestContext": {"http": {"method": method, "path": path}},
        "pathParameters": path_params,
        "body": json.dumps(body) if body is not None else None,
    }


_TABLES["Books"]["b1"] = {"id": "b1", "title": "Release It!", "price": 34.99}

r = catalog.handler(evt("GET", "/books"), None)
check("GET /books returns 200", r["statusCode"] == 200)
check("GET /books lists the seeded book", "Release It!" in r["body"])

r = catalog.handler(evt("GET", "/books/b1", {"id": "b1"}), None)
check("GET /books/{id} returns 200", r["statusCode"] == 200)

r = catalog.handler(evt("GET", "/books/nope", {"id": "nope"}), None)
check("GET unknown book returns 404", r["statusCode"] == 404)

r = orders.handler(evt("POST", "/orders", body={"book_id": "b1", "qty": 2}), None)
check("POST /orders returns 201", r["statusCode"] == 201)
order_id = json.loads(r["body"])["id"]

r = orders.handler(evt("GET", "/orders/" + order_id, {"id": order_id}), None)
check("GET /orders/{id} returns the order", r["statusCode"] == 200)

r = orders.handler(evt("POST", "/orders", body={"book_id": "ghost"}), None)
check("POST with unknown book_id returns 400", r["statusCode"] == 400)

b64 = evt("POST", "/orders")
b64["body"] = base64.b64encode(json.dumps({"book_id": "b1", "qty": 1}).encode()).decode()
b64["isBase64Encoded"] = True
r = orders.handler(b64, None)
check("POST with base64-encoded body (no JSON content-type) returns 201", r["statusCode"] == 201)

bad = evt("POST", "/orders")
bad["body"] = "not json"
r = orders.handler(bad, None)
check("POST with non-JSON body returns 400, not 500", r["statusCode"] == 400)

print(f"\n{_PASS} passed, {_FAIL} failed")
sys.exit(1 if _FAIL else 0)
