# Step 2 — Deploy BuggyLambda and Trigger Each Failure Scenario

`buggy_functions.py` routes to a different failure path based on the `scenario` key in the event. You'll invoke each scenario, observe the error, and know where to look in CloudWatch Logs.

---

## 2.1 Package the Code

```bash
cd /path/to/lambda-troubleshooting-monitoring
zip -j buggy_functions.zip src/buggy_functions.py
```

---

## 2.2 Create the Function in the Console

1. Open **Lambda** → **Create function** → **Author from scratch**.

   | Field | Value |
   |-------|-------|
   | Function name | `BuggyLambda` |
   | Runtime | **Python 3.14** |
   | Architecture | x86_64 |

2. Under **Permissions → Change default execution role**:

   | Field | Value |
   |-------|-------|
   | Execution role | **Use an existing role** |
   | Existing role | `LambdaTroubleshootingRole` |

3. Click **Create function**.

---

## 2.3 Upload the Code

1. **Code source** → **Upload from** → **.zip file** → select `buggy_functions.zip` → **Save**.
2. **Configuration → General configuration → Edit**:

   | Field | Value |
   |-------|-------|
   | Handler | `buggy_functions.handler` |
   | Memory | 128 MB |
   | Timeout | **10 sec** (important — the `timeout` scenario relies on this) |

3. Click **Save**.

---

## 2.4 Scenario Reference

| Scenario key | What breaks | What you see in CloudWatch |
|---|---|---|
| `ok` | Nothing | Normal log lines, short duration |
| `unhandled_error` | `ValueError` raised | `[ERROR]` + traceback, `FunctionError: Unhandled` |
| `timeout` | Sleeps 60s (timeout=10s) | `Task timed out after 10.00 seconds` |
| `memory_oom` | Allocates until killed | `Runtime exited with error: signal: killed` |
| `missing_env` | `KeyError` on `DATABASE_URL` | `[ERROR] KeyError: 'DATABASE_URL'` |
| `bad_json` | Returns `datetime` object | `TypeError: Object of type datetime is not JSON serializable` |
| `divide_by_zero` | ZeroDivisionError | `[ERROR] ZeroDivisionError: division by zero` |
| `partial_success` | Some items fail | HTTP 207 with failures array |

---

## 2.5 Test Each Scenario via the Console

Create a test event for each scenario below. Go to the **Test** tab → **Create new event**.

### Scenario: `ok` (happy path)

Event name: `ScenarioOK`

```json
{ "scenario": "ok" }
```

Expected: `{"statusCode": 200, "body": "{\"message\": \"All good!\"}"}` — no errors.

---

### Scenario: `unhandled_error`

Event name: `ScenarioError`

```json
{ "scenario": "unhandled_error" }
```

The Execution result shows **Function error: Unhandled** in red. The Log output contains:

```
[ERROR] ValueError: Something went wrong — this is intentional for learning.
```

> Note: the HTTP invocation status is still **200** (Lambda delivered the invocation). The `FunctionError` indicates the function itself crashed. This distinction is critical for debugging.

---

### Scenario: `timeout`

Event name: `ScenarioTimeout`

```json
{ "scenario": "timeout" }
```

This takes exactly **10 seconds** to return (the configured timeout). The REPORT line shows:

```
Duration: 10000.00 ms  Billed Duration: 10000 ms
```

And the error message: `Task timed out after 10.00 seconds`.

---

### Scenario: `memory_oom`

Event name: `ScenarioOOM`

```json
{ "scenario": "memory_oom" }
```

Lambda kills the container when memory is exhausted. In CloudWatch look for:

```
Runtime exited with error: signal: killed (SIGKILL)
```

The REPORT line shows `Max Memory Used: 128 MB` (equal to Memory Size — fully consumed).

---

### Scenario: `divide_by_zero`

Event name: `ScenarioDivide`

```json
{ "scenario": "divide_by_zero", "numerator": 10, "denominator": 0 }
```

`FunctionError: Unhandled` with `ZeroDivisionError`. Now test with a valid denominator:

```json
{ "scenario": "divide_by_zero", "numerator": 10, "denominator": 2 }
```

No error — result is `5.0`.

---

### Scenario: `partial_success`

Event name: `ScenarioPartial`

```json
{
  "scenario": "partial_success",
  "items": ["item1", "bad-item", "item2"]
}
```

Returns HTTP 207 (not an error from Lambda's perspective):

```json
{
  "statusCode": 207,
  "body": "{\"successes\": [\"item1\", \"item2\"], \"failures\": [{\"item\": \"bad-item\", \"error\": \"Validation failed\"}]}"
}
```

In CloudWatch you'll see an `[ERROR]` for the bad item but the function itself returned cleanly.

---

## 2.6 Verify All Errors Appear in CloudWatch

1. **Lambda → BuggyLambda → Monitor → View CloudWatch logs**.
2. Open any stream and look for `[ERROR]` lines.
3. Notice how each error has a different `errorType` — this is what you'd filter on in Log Insights (Step 4).

---

## Checkpoint

- [ ] `BuggyLambda` deployed and Active with 10-second timeout
- [ ] All 6 non-destructive scenarios invoked and errors observed
- [ ] Understood why HTTP 200 can coexist with `FunctionError`
- [ ] Found `[ERROR]` lines in CloudWatch for each failure scenario

---

**Next:** [Step 3 — Reading CloudWatch Logs](./03-cloudwatch-logs.md)
