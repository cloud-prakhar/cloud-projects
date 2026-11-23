# Step 5 — Build the Orders Lambda

The second slice. `bookstore-orders` serves the monolith's `/orders` routes: create an order
(`POST /orders`) and read one (`GET /orders/{id}`). Before it writes an order it **reads the
`Books` table** to confirm the `book_id` exists — the same validation the monolith did with a
SQL join, now an explicit cross-table read. This is why its role (Step 3) has read access to
`Books`.

---

## 5.1 What You're Creating

| Setting | Value |
|---------|-------|
| Function name | `bookstore-orders` |
| Runtime | `python3.14` |
| Handler | `handler.handler` |
| Role | `BookstoreOrdersRole` (Step 3) |
| Env vars | `ORDERS_TABLE=Orders`, `BOOKS_TABLE=Books`, `APP_VERSION=orders-1.0` |
| Code | `src/orders/handler.py` |

---

## 5.2 Package + Create

`orders.zip` is **not** in the repo (`*.zip` is git-ignored) — you create it here from
`src/orders/handler.py`. Run this from the **project root**
(`projects/advanced/aws/aws-monolith-to-serverless-migration/`). If you're still inside
`src/catalog/` from Step 4, run `cd ../..` first — otherwise `cd src/orders` fails with
`No such file or directory` and no zip is produced.

```bash
cd src/orders
zip orders.zip handler.py
ls -l orders.zip
unzip -l orders.zip
```

`unzip -l` must list `handler.py` at the **top level** of the archive (not
`src/orders/handler.py`) — Lambda resolves `handler.handler` as *file* `handler.py`, *function*
`handler`, from the zip root.

> **WSL / Windows users:** the Console's file picker runs in Windows, so browse to the WSL path
> (`\\wsl$\<distro>\home\<you>\...\src\orders\orders.zip`), or run `explorer.exe .` from
> `src/orders` to open that folder in Explorer.

### Console

1. **Lambda → Create function → Author from scratch.**
2. **Name:** `bookstore-orders`. **Runtime:** Python 3.14.
3. **Use an existing role →** `BookstoreOrdersRole` → **Create function**.
4. **Code → Upload from → .zip** → `orders.zip`. **Handler:** `handler.handler`.
5. **Environment variables:** `ORDERS_TABLE=Orders`, `BOOKS_TABLE=Books`,
   `APP_VERSION=orders-1.0` → **Save**.

### CLI alternative

```bash
aws lambda create-function \
  --function-name bookstore-orders \
  --runtime python3.14 --handler handler.handler \
  --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/BookstoreOrdersRole \
  --zip-file fileb://orders.zip \
  --environment "Variables={ORDERS_TABLE=Orders,BOOKS_TABLE=Books,APP_VERSION=orders-1.0}"
```

---

## 5.3 Test It

Create an order (use a real `book_id` from Step 2):

```json
{
  "requestContext": { "http": { "method": "POST", "path": "/orders" } },
  "body": "{\"book_id\":\"<real-id>\",\"qty\":2}"
}
```

Expect `201` and a new order id. Then test the unhappy path — a fake `book_id` should return
`400 unknown book_id` (proving the cross-table validation works). Finally read it back with a
`GET /orders/{id}` event (`pathParameters: {"id": "<order-id>"}`).

### CLI alternative

```bash
aws lambda invoke --function-name bookstore-orders \
  --payload '{"requestContext":{"http":{"method":"POST","path":"/orders"}},"body":"{\"book_id\":\"<real-id>\",\"qty\":2}"}' \
  --cli-binary-format raw-in-base64-out out.json
cat out.json
```

> **Why validate `book_id` here and not at the API layer?** Business rules belong to the
> service that owns the operation. Orders owns "you can't order a book that doesn't exist," so
> orders enforces it — and it reads catalog data read-only to do so.

---

## Checkpoint

- [ ] `bookstore-orders` exists with `BookstoreOrdersRole`
- [ ] `POST /orders` with a valid `book_id` returns `201`
- [ ] `POST /orders` with a bogus `book_id` returns `400`
- [ ] `GET /orders/{id}` returns the created order
- [ ] Both Lambdas now reproduce the monolith's behavior — ready to put a front door on them

---

**Next:** [Step 6 — HTTP API Front Door + Strangler Cutover](./06-http-api-strangler.md)
