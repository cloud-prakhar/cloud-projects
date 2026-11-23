# Step 4 — Build the Catalog Lambda

Now the first strangler vine grows. You'll deploy `bookstore-catalog` — a Lambda that serves
exactly the routes the monolith served under `/books*`, but reads from the `Books` DynamoDB
table instead of SQLite. Same contract, new engine. The monolith keeps running; this just
gives the front door (Step 6) a serverless option to point `/books*` at.

---

## 4.1 What You're Creating

| Setting | Value |
|---------|-------|
| Function name | `bookstore-catalog` |
| Runtime | `python3.14` |
| Handler | `handler.handler` |
| Role | `BookstoreCatalogRole` (Step 3) |
| Env var | `BOOKS_TABLE=Books`, `APP_VERSION=catalog-1.0` |
| Code | `src/catalog/handler.py` |

---

## 4.2 Package the Code

The handler uses only `boto3` (in the Lambda runtime already), so the zip is just the file:

You create `catalog.zip` yourself — it isn't committed (`*.zip` is git-ignored). Run from the
**project root** (`projects/advanced/aws/aws-monolith-to-serverless-migration/`):

```bash
cd src/catalog
zip catalog.zip handler.py
unzip -l catalog.zip
```

`handler.py` must sit at the top level of the zip so `handler.handler` resolves. Stay in
`src/catalog/` for the CLI `create-function` below (`fileb://catalog.zip` is a relative path),
then `cd ../..` back to the project root before Step 5.

---

## 4.3 Console — Create the Function

1. **Lambda → Create function → Author from scratch.**
2. **Name:** `bookstore-catalog`. **Runtime:** Python 3.14.
3. **Permissions → Use an existing role →** `BookstoreCatalogRole` → **Create function**.
4. **Code → Upload from → .zip file →** upload `catalog.zip`.
5. **Runtime settings → Edit → Handler:** `handler.handler`.
6. **Configuration → Environment variables → Edit → Add:**
   `BOOKS_TABLE=Books`, `APP_VERSION=catalog-1.0` → **Save**.

### CLI alternative

```bash
aws lambda create-function \
  --function-name bookstore-catalog \
  --runtime python3.14 --handler handler.handler \
  --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/BookstoreCatalogRole \
  --zip-file fileb://catalog.zip \
  --environment "Variables={BOOKS_TABLE=Books,APP_VERSION=catalog-1.0}"
```

---

## 4.4 Test It

**Console → Test** with this HTTP-API-v2.0 event (list):

```json
{ "requestContext": { "http": { "method": "GET", "path": "/books" } } }
```

Expect `statusCode: 200` and the three migrated books in the body. Then test a single book by
adding `"pathParameters": {"id": "<a-real-id>"}` and path `/books/<id>`.

### CLI alternative

```bash
aws lambda invoke --function-name bookstore-catalog \
  --payload '{"requestContext":{"http":{"method":"GET","path":"/books"}}}' \
  --cli-binary-format raw-in-base64-out out.json
cat out.json
```

---

## Checkpoint

- [ ] `bookstore-catalog` exists with handler `handler.handler` and `BookstoreCatalogRole`
- [ ] A `GET /books` test event returns `200` with the migrated books
- [ ] A `GET /books/{id}` test returns the right book (and `404` for a bad id)
- [ ] CloudWatch shows a log group `/aws/lambda/bookstore-catalog`

---

**Next:** [Step 5 — Build the Orders Lambda](./05-orders-lambda.md)
