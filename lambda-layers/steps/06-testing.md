# Step 6 — Testing Layer-Backed Functions

---

## Test RequestsFunction

```bash
aws lambda invoke \
  --function-name RequestsFunction \
  --cli-binary-format raw-in-base64-out \
  --payload '{"url": "https://httpbin.org/get"}' \
  /tmp/requests_response.json

cat /tmp/requests_response.json | python3 -m json.tool
```

Expected response body:

```json
{
  "fetched_url": "https://httpbin.org/get",
  "http_status": 200,
  "response_preview": "{'args': {}, 'headers': {...}, 'url': 'https://httpbin.org/get'}"
}
```

If the function errors with `ModuleNotFoundError: No module named 'requests'`, the layer is not attached — see troubleshooting.

---

## Test PandasFunction

```bash
aws lambda invoke \
  --function-name PandasFunction \
  --cli-binary-format raw-in-base64-out \
  --payload '{
    "csv_data": "product,price,quantity\nWidget,9.99,100\nGadget,49.99,50\nDoohickey,4.99,200"
  }' \
  /tmp/pandas_response.json

cat /tmp/pandas_response.json | python3 -m json.tool
```

Expected response body:

```json
{
  "rows": 3,
  "columns": 3,
  "column_names": ["product", "price", "quantity"],
  "numeric_columns": ["price", "quantity"],
  "statistics": {
    "price":    {"count": 3.0, "mean": 21.6567, "std": 23.4, "min": 4.99, ...},
    "quantity": {"count": 3.0, "mean": 116.6667, ...}
  }
}
```

---

## Observe Init Duration (Cold Start)

Look at the CloudWatch Logs REPORT line after the first invocation:

```bash
LOG_GROUP="/aws/lambda/PandasFunction"
STREAM=$(aws logs describe-log-streams \
  --log-group-name "$LOG_GROUP" \
  --order-by LastEventTime \
  --descending \
  --query 'logStreams[0].logStreamName' \
  --output text)

aws logs get-log-events \
  --log-group-name "$LOG_GROUP" \
  --log-stream-name "$STREAM" \
  --query 'events[*].message' \
  --output text | grep -E "REPORT|Init Duration"
```

You'll see something like:

```
REPORT RequestId: ...  Duration: 412.55 ms  Billed Duration: 413 ms  Memory Size: 512 MB  Max Memory Used: 198 MB  Init Duration: 1842.31 ms
```

`Init Duration: 1842 ms` — nearly 2 seconds to import pandas and numpy during the cold start. Warm invocations will complete in under 100 ms. This is why heavy libraries increase cold start times.

---

## Invoke the Second Time (Warm)

```bash
aws lambda invoke \
  --function-name PandasFunction \
  --cli-binary-format raw-in-base64-out \
  --payload '{"csv_data": "a,b\n1,2\n3,4"}' \
  /tmp/warm_response.json

# Check logs again — Init Duration should be absent
aws logs get-log-events \
  --log-group-name "/aws/lambda/PandasFunction" \
  --log-stream-name "$STREAM" \
  --query 'events[*].message' \
  --output text | grep REPORT | tail -1
```

---

## Checkpoint

- [ ] `RequestsFunction` successfully fetched a URL via the `requests` layer
- [ ] `PandasFunction` processed CSV data and returned statistics via the `pandas` layer
- [ ] Observed Init Duration on cold start and its absence on warm invocation

---

**Next →** [07-cleanup.md](07-cleanup.md)
