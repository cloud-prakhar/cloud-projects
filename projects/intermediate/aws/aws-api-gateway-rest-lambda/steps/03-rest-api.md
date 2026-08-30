# Step 3 — Build the REST API

A REST API in API Gateway is a tree of **resources** (URL paths), each with one or more
**methods** (HTTP verbs), each wired to an **integration** (here, our Lambda). We use
**Lambda proxy integration** — the simplest and most common choice — which forwards the
*entire* request to the function and returns whatever the function says, verbatim.

> **Proxy vs non-proxy:** With proxy integration, API Gateway does no request/response
> mapping — your code owns it (that's why `app.py` reads `httpMethod`/`path` and returns
> `{statusCode, headers, body}`). Non-proxy ("Lambda integration") makes you write mapping
> templates in the console. Proxy keeps the logic in code where you can test it — which is
> exactly what `test_app.py` does.

---

## 3.1 Console — Create the API

1. **API Gateway → Create API → REST API → Build**.
2. **API name:** `quotes-rest-api` → **Endpoint type:** Regional → **Create API**.

You now have an empty API with just a `/` root resource.

---

## 3.2 Create Resources and Methods

We need three paths: `/quotes`, `/quotes/{id}`, and `/version`.

**Create `/quotes`:**

1. Select the `/` resource → **Create resource**.
2. **Resource name:** `quotes` → **Create resource**.

**Create `/quotes/{id}`** (a path parameter):

1. Select `/quotes` → **Create resource**.
2. **Resource name:** `id`, **Resource path:** `{id}` → **Create resource**.

**Create `/version`:**

1. Select `/` → **Create resource** → name `version` → **Create resource**.

**Now add methods** (each one a Lambda proxy integration to `quotes-api`):

| Resource | Method | Integration |
|----------|--------|-------------|
| `/quotes` | GET | Lambda proxy → `quotes-api` |
| `/quotes` | POST | Lambda proxy → `quotes-api` |
| `/quotes/{id}` | GET | Lambda proxy → `quotes-api` |
| `/version` | GET | Lambda proxy → `quotes-api` |

For each row: select the resource → **Create method** → choose the verb → **Integration
type: Lambda** → toggle **Lambda proxy integration ON** → pick `quotes-api` → **Create
method**. Approve the "give API Gateway permission to invoke" prompt — that adds a
resource-based policy on the Lambda.

---

## 3.3 Test from the API Gateway Console

Before deploying, use the built-in tester:

1. Select **`/quotes` → GET → Test** (the lightning-bolt **Test** tab).
2. Click **Test**. You should see a `200` and the two-quote JSON body.

This runs the integration without a public URL yet — handy for catching wiring mistakes.

> **Enjoy the Test button while it works.** In Step 4 you'll repoint the integration at a Lambda
> alias through a **stage variable**, and the Test tab invokes methods *outside* any stage — so
> from then on it returns a `400` validation error unless you hand it the stage variable
> yourself. Step 4 explains why and what to use instead.

---

## 3.4 AWS CLI (Alternative — minimal version)

The console is far easier for building a resource tree, but here's the shape of it:

```bash
REGION=us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

API_ID=$(aws apigateway create-rest-api --name quotes-rest-api \
  --endpoint-configuration types=REGIONAL \
  --query 'id' --output text --region $REGION)
echo "API_ID=$API_ID"   # SAVE THIS

# ...create resources (create-resource), methods (put-method),
#    and integrations (put-integration) for each path...
# Grant API Gateway permission to invoke the function:
aws lambda add-permission --function-name quotes-api \
  --statement-id apigw-invoke --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" --region $REGION
```

> Full CLI for a multi-resource REST API is verbose; the console walkthrough above is the
> recommended path. **Save `API_ID`** — every later step uses it.

---

## Checkpoint

- [ ] REST API `quotes-rest-api` exists; you saved its **API ID**
- [ ] Resources `/quotes`, `/quotes/{id}`, `/version` exist
- [ ] Methods GET/POST on `/quotes`, GET on `/quotes/{id}`, GET on `/version` — all Lambda **proxy**
- [ ] The console **Test** on `GET /quotes` returns `200`

---

**Next:** [Step 4 — Deploy to a Stage](./04-deploy-stages.md)
