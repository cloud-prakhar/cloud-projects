# Troubleshooting — Monolith → Serverless Migration

Format: **Error → Cause → Fix.** Every entry below was hit and fixed on a real run of this
project, so the symptoms are the exact strings you'll see.

## Start here — the three that catch almost everyone

| If you see… | It's almost certainly… | Jump to |
|---|---|---|
| `{"message":"Not Found"}` on **every** API route | You built the API on the CLI and it has **no stage** | [no stage](#api-gateway-messagenot-found-on-every-route-built-via-cli) |
| Monolith and API return different JSON **types** (`"39.99"` vs `39.99`) | `default=str` stringifying DynamoDB `Decimal`s | [parity](#parity-check-fails-price-comes-back-as-a-string-3999-not-3999) |
| DynamoDB has **more** orders than SQLite in Step 7 | Nothing — counts are *supposed* to diverge after cutover | [reconciliation](#reconciliation-dynamodb-has-more-orders-than-sqlite) |

<details>
<summary><strong>Full list of entries</strong></summary>

**Step 1 — monolith on EC2**
- Instance type not supported in your AZ
- `curl http://<ip>:5000/books` times out

**Step 2 — data migration**
- `Float types are not supported. Use Decimal types instead`

**Steps 3–5 — IAM and Lambda**
- `AccessDeniedException` on DynamoDB
- `ResourceNotFoundException` (table)
- Every `POST /orders` returns `400 unknown book_id`

**Step 6 — API Gateway and cutover**
- `{"message":"Not Found"}` on every route (no stage)
- `{"message":"Not Found"}` on one route only
- `500 Internal Server Error` but the Lambda test worked
- `GET /books` works but `GET /books/{id}` returns 500
- Catch-all returns `503 Service Unavailable`
- HTTP_PROXY integration rejected at creation
- Will the catch-all swallow migrated routes?
- Parity check fails: `price` comes back as a string
- After Vine 2, an earlier order returns `404` (route moved, data didn't yet)
- Vine applied but `curl` still shows `monolith-1.0` (propagation)

**Steps 7–8 — decommission and cleanup**
- Reconciliation: DynamoDB has more orders than SQLite
- An order placed on the monolith is missing in DynamoDB
- `DependencyViolation` deleting the security group

</details>

---

### Monolith: `curl http://<ip>:5000/books` times out

**Cause:** Security group doesn't allow port 5000 from your IP, or Flask is bound to
`127.0.0.1` instead of `0.0.0.0`.

**Fix:** Add an inbound rule `Custom TCP 5000` from **My IP** on the instance's security group.
Confirm the app prints `Running on http://0.0.0.0:5000` — `app.run(host="0.0.0.0", ...)` is set
in `app.py`. If you used SSM-only (no SSH), reach it via Session Manager + `curl localhost:5000`.

---

### Data migration: `Float types are not supported. Use Decimal types instead`

**Cause:** DynamoDB's number type maps to Python `Decimal`. The SQLite `price` comes back as a
`float`, which `put_item` rejects.

**Fix:** Convert via string — `Decimal(str(row["price"]))`, as the Step 2 script does. Never
`Decimal(float_value)` directly (that carries the float's imprecision).

---

### Packaging: can't find `orders.zip` / `catalog.zip`, or `cd src/orders: No such file or directory`

**Cause:** The zips aren't in the repo (`*.zip` is git-ignored). You build them yourself in
Step 4.2 / 5.2. The `cd src/...` commands are relative to the **project root**, so if you're
still in `src/catalog/` from Step 4, `cd src/orders` fails and `zip` never runs.

**Fix:** Go back to the project root (`cd ../..` from `src/catalog`), then
`cd src/orders && zip orders.zip handler.py`. Run `unzip -l orders.zip` to check that
`handler.py` sits at the top level of the zip. If it's nested (e.g. `src/orders/handler.py`),
Lambda returns `Runtime.ImportModuleError: No module named 'handler'`.

---

### Data migration: `AccessDeniedException … dynamodb:BatchWriteItem` on the EC2 box

**Cause:** `BookstoreMonolithRole` only has `AmazonSSMManagedInstanceCore`. `batch_writer()`
needs `dynamodb:BatchWriteItem`, and the script's final count needs `dynamodb:Scan`.

**Fix:** Add the `BookstoreMigrationWrite` inline policy from Step 2.3. Wait about 10 seconds
for IAM to propagate, then re-run `migrate_data.py`. It's idempotent.

---

### Step 7: `sqlite3: command not found` / `s3 cp … AccessDenied`

**Cause:** Amazon Linux 2023 doesn't ship the `sqlite3` command. Separately, the instance role
has no S3 permissions.

**Fix:** Run `sudo dnf install -y sqlite` (Step 1.3 now includes it), and add the
`BookstoreSnapshotWrite` policy from Step 7.2 before running `aws s3 cp`.

---

### Orders: `POST /orders` through the API returns `500`, but the Lambda console test returns `400`/`201`

**Symptom:** `curl -X POST $BASE/orders -d '{"book_id":"…"}'` returns
`{"message":"Internal Server Error"}`. The logs show `JSONDecodeError: Expecting value`.

**Cause:** Without a JSON `content-type`, HTTP API **base64-encodes** the body and sets
`isBase64Encoded: true`, so a handler that `json.loads` the raw body crashes. The monolith
(`get_json(force=True)`) accepted the same request, so this is a parity break.

**Fix:** The shipped `src/orders/handler.py` decodes base64 bodies and returns `400` for
non-JSON. Redeploy it if you wrote your own handler
(`zip orders.zip handler.py && aws lambda update-function-code --function-name bookstore-orders --zip-file fileb://orders.zip`).
Clients should also send `-H 'content-type: application/json'`.

---

### After Vine 2, `GET /orders/{id}` returns `404` for an order you placed earlier

**Cause:** Expected. You placed that order during Vine 0 or Vine 1, when `/orders*` still went
through the catch-all to the monolith, so it lives in **SQLite only**. Moving the route didn't
move the data.

**Fix:** None needed in Step 6. Step 7.1 re-runs the idempotent exporter. After that, the same
`curl $BASE/orders/<id>` returns `200`.

---

### Vine just applied but `curl` still shows `monolith-1.0`

**Cause:** Auto-deploy takes a few seconds to go live after `create-route`/`delete-route`.

**Fix:** Wait ~5 seconds and retry. If it persists, check that the route exists
(`aws apigatewayv2 get-routes --api-id $API_ID --query "Items[].RouteKey"`) and has a target.

---

### Cleanup: `DeleteConflict … must delete policies first` deleting `BookstoreMonolithRole`

**Cause:** The role still has inline policies (`BookstoreMigrationWrite`,
`BookstoreSnapshotWrite`). `detach-role-policy` only removes *managed* policies.

**Fix:** Run `aws iam delete-role-policy` for each inline policy (Step 8.5), then `delete-role`.

---

### Lambda: `AccessDeniedException` on DynamoDB in the catalog/orders logs

**Cause:** The execution role's inline policy is missing, scoped to the wrong table ARN, or has
the wrong account id.

**Fix:** Re-check Step 3. `BookstoreCatalogRole` must allow `GetItem`/`Scan` on
`.../table/Books`; `BookstoreOrdersRole` must allow `GetItem`/`PutItem` on `.../table/Orders`
**and** `GetItem` on `.../table/Books`. No `Resource: "*"`.

---

### Lambda: `ResourceNotFoundException` (table)

**Cause:** The `BOOKS_TABLE`/`ORDERS_TABLE` env var doesn't match the real table name, or the
table is in another region.

**Fix:** Confirm env vars (`Books`, `Orders`) and that the tables live in `us-east-1`. Note
`update-function-configuration` **replaces** all env vars — re-setting one drops the others.

---

### Orders Lambda: every `POST /orders` returns `400 unknown book_id`

**Cause:** The orders function can't *read* `Books` (missing the second statement in its role),
so the validation lookup returns nothing — or you're posting an id that wasn't migrated.

**Fix:** Confirm `BookstoreOrdersRole` includes `GetItem` on the `Books` ARN. Confirm the
`book_id` you POST actually exists: `aws dynamodb get-item --table-name Books --key '{"id":{"S":"<id>"}}'`.

---

### API Gateway: `{"message":"Not Found"}` on **every** route (built via CLI)

**Symptom:** You created the API on the CLI, every route looks right in `get-routes`, and yet
*every single request* — `/books`, `/orders`, anything — returns `404 {"message":"Not Found"}`.

**Cause:** Your API has **no stage**. This is the single most common way to get stuck in Step 6,
and it's easy to miss because the console and the CLI behave differently:

- Creating an HTTP API in the **Console** silently creates a `$default` stage and auto-deploys.
- Creating one with `aws apigatewayv2 create-api` does **not** create any stage.

An API with good routes but no stage has nowhere to serve them from, so the router rejects
everything before it ever reaches your routes. The error looks identical to a broken route,
which is why people rebuild their routes over and over without fixing anything.

**Diagnose it in one command** — this is the tell:

```bash
aws apigatewayv2 get-stages --api-id $API_ID --query "Items[].StageName"
# []   <- empty list = this is your problem
```

**Fix:**

```bash
aws apigatewayv2 create-stage --api-id $API_ID --stage-name '$default' --auto-deploy
```

Quote `'$default'` — unquoted, your shell expands `$default` to an empty string and the CLI
rejects it. `--auto-deploy` is what makes later route changes go live automatically.

Then confirm the URL has **no** stage segment:
`https://<api-id>.execute-api.us-east-1.amazonaws.com/books`

---

### API Gateway: `{"message":"Not Found"}` on **one** route only

**Cause:** That specific route key doesn't exist or has no integration attached — e.g. you
created `GET /books` but not `GET /books/{id}`, or a route shows no target.

**Fix:** List what's actually there and compare against the four routes Step 6 needs:

```bash
aws apigatewayv2 get-routes --api-id $API_ID \
  --query "Items[].{route:RouteKey,target:Target}" --output table
```

You want exactly: `GET /books`, `GET /books/{id}`, `POST /orders`, `GET /orders/{id}`, each with
a non-empty target. In the Console, **Develop → Routes** should show an integration on each.

---

### API Gateway: `500 Internal Server Error` but the Lambda test worked

**Cause:** Payload shape mismatch — the function reads `event["requestContext"]["http"]["method"]`
(payload v2.0). A REST API or a v1.0 integration sends a different shape.

**Fix:** Ensure the integration is **payload format version 2.0** (the HTTP API default for
Lambda proxy). Check the function's CloudWatch logs for the actual `KeyError`.

---

### Parity check fails: `price` comes back as a string (`"39.99"` not `39.99`)

**Symptom:** Step 6.7 says the monolith and API responses should match, but they don't:

```
monolith: {"price": 39.99,   "title": "The Pragmatic Programmer"}
api     : {"price": "39.99", "title": "The Pragmatic Programmer"}
```

Status codes match, so it's easy to wave through — but a client doing `price * qty` will start
throwing after cutover.

**Cause:** DynamoDB returns numbers to Python as `Decimal`, which `json.dumps` cannot serialise
on its own. The tempting one-character fix is `json.dumps(body, default=str)` — and `str` turns
every `Decimal` into a **string**, silently changing the API contract. The same thing happens to
`qty`, which becomes `"3"` instead of `3`.

**Fix:** Convert `Decimal` back to a real number instead of stringifying it. The handlers in
`src/` do this:

```python
from decimal import Decimal

def _json_default(value):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    return str(value)

json.dumps(body, default=_json_default)
```

The `% 1 == 0` test keeps whole numbers as `int` (so `qty` is `3`, not `3.0`) while prices keep
their decimals. If you changed the handlers yourself and hit this, redeploy and re-check:

```bash
aws lambda update-function-code --function-name bookstore-catalog --zip-file fileb://catalog.zip
aws lambda wait function-updated --function-name bookstore-catalog
```

> **Why this earns its own entry:** "Backward compatibility during migration" is the principle
> that makes a strangler cutover safe. A type change is the quietest possible way to break it.

---

### Reconciliation: DynamoDB has *more* orders than SQLite

**Symptom:** In Step 7 you compare counts and they don't match — DynamoDB has more. It looks
like something duplicated your data.

**Cause:** Nothing is wrong. After cutover, DynamoDB holds the orders exported from the monolith
**plus** every order placed through the new API — and those never existed in SQLite. Counts
*should* diverge. Comparing them with `COUNT(*)` on both sides will fail forever.

**Fix:** Check for **data loss**, not for equality. Every SQLite order id must exist in
DynamoDB; extra DynamoDB ids are expected and fine.

```bash
sqlite3 bookstore.db "SELECT id FROM orders;" | sort > /tmp/sqlite_ids.txt
aws dynamodb scan --table-name Orders --query "Items[].id.S" --output text \
  | tr '\t' '\n' | sort > /tmp/ddb_ids.txt
comm -23 /tmp/sqlite_ids.txt /tmp/ddb_ids.txt    # must print nothing
```

Empty output = zero data loss = safe to terminate the instance.

---

### EC2 launch fails: "instance type not supported in your requested Availability Zone"

**Cause:** Not every AZ offers every instance type. In `us-east-1`, `t3.micro` is unavailable in
**`us-east-1e`**. You'll usually hit this on the CLI, where grabbing the "first" subnet in the
default VPC can land you in that AZ.

**Fix:** Omit the subnet and let AWS place the instance, or pin a known-good AZ:

```bash
SUBNET=$(aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=<vpc-id> Name=availability-zone,Values=us-east-1a \
  --query "Subnets[0].SubnetId" --output text)
```

`t3.micro` works in `us-east-1a/b/c/d/f`.

---

### API Gateway: `GET /books` works but `GET /books/{id}` returns 500

**Cause:** The `lambda add-permission` source ARN was scoped to the exact path `.../books` and
doesn't cover the sub-path, so API Gateway isn't authorised to invoke the function for that
route. (Only bites the CLI path — the Console adds permissions per route automatically.)

**Fix:** Use a trailing `*` so one statement covers both routes:

```bash
--source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/*/books*"
```

Delete the old statement first if you need to replace it:
`aws lambda remove-permission --function-name bookstore-catalog --statement-id apigw-books`

---

### Cleanup: `DependencyViolation` deleting the security group

**Cause:** The instance is still shutting down. A security group can't be deleted until nothing
uses it, and `terminate-instances` returns immediately while termination continues in the
background.

**Fix:** Wait for the instance to actually reach `terminated`, then delete:

```bash
aws ec2 wait instance-terminated --instance-ids <id>
aws ec2 delete-security-group --group-id <sg-id>
```

The same ordering rule applies to IAM: detach policies before deleting a role, and remove the
role from an instance profile before deleting the profile.

---

### After cutover, an order placed on the monolith is missing in DynamoDB

**Cause:** It was created **after** your Step 2 export but **before** cutover — the classic
"data drift during migration" gap.

**Fix:** Re-run the idempotent exporter (Step 7 reconciliation) before terminating the monolith.
Counts must match. This is exactly why Step 7 reconciles twice.

---

### HTTP_PROXY catch-all to the monolith returns `503 Service Unavailable`

**Symptom:** The catch-all route from Step 6.3 (Vine 0) returns
`{"message":"Service Unavailable"}` (503), even though you can `curl` the monolith fine from
your own laptop.

**Cause:** Your security group allows port 5000 from **My IP** only. API Gateway calls your
instance from **AWS's network**, not from your laptop, so the TCP connection is refused. Other
causes with the same symptom: the instance is stopped, or the port in the integration URI is
wrong.

**How to tell it's the route vs. the network** — this distinction saves a lot of time:

| What you get | What it means |
|---|---|
| `404 {"message":"Not Found"}` | The **route didn't match**. Your catch-all isn't configured. |
| `503 {"message":"Service Unavailable"}` | The route **did** match and API Gateway **tried** to connect — it's a network/reachability problem, not a routing one. |

**Fix:** Pick one:

- **Skip Vine 0 and Vine 3.** The four Lambda routes still complete the migration; the vines just become checkpoints instead of a live cutover.
- **Allow the published API Gateway ranges.** AWS lists them in `ip-ranges.json` under service
  `API_GATEWAY` (about 16 CIDRs for `us-east-1`). Step 6.3 has a copy-paste command that adds
  them to the security group on port 5000. Tested: the catch-all goes from `503` to `200`
  without opening `0.0.0.0/0`. These ranges are shared by all API Gateway customers and change
  over time, so this is fine for the throwaway lab box but is not access control.
- **Do it properly with a VPC Link** (private integration to an ALB/NLB in your VPC), so the
  monolith needs no public listener at all. This is the production-safe shape.

Once all routes are migrated, **delete the catch-all** instead of fixing it — that deletion
*is* the cutover completing.

---

### HTTP_PROXY integration rejected at creation

**Cause:** `HTTP_PROXY` integrations have two requirements Lambda integrations don't:
`--integration-method` is **mandatory**, and they use **payload format 1.0**, not the 2.0 your
Lambda handlers expect.

**Fix:**

```bash
aws apigatewayv2 create-integration --api-id $API_ID \
  --integration-type HTTP_PROXY --integration-method ANY \
  --integration-uri "http://<ec2-ip>:5000/{proxy}" \
  --payload-format-version 1.0
```

---

### Worried the catch-all will swallow your migrated routes?

It won't. API Gateway matches the **most specific** route first, so `GET /books` goes to
`bookstore-catalog` while `GET /health` — which has no explicit route — falls through to the
monolith. That precedence is exactly what makes route-by-route migration possible, and it's
worth confirming yourself: with the catch-all in place, `curl $BASE/books` should still return
`catalog-1.0` in the body, not the monolith's `monolith-1.0`.
