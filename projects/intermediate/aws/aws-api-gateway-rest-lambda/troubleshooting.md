# Troubleshooting — API Gateway REST API + Lambda

Format: **Error → Cause → Fix.**

---

### `500 Internal server error` (and CloudWatch shows no Lambda invocation)

**Cause:** API Gateway tried to invoke a Lambda **alias** it has no permission for. When you
switched the integration to the stage-variable ARN
`arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:quotes-api:${stageVariables.lambdaAlias}`
(Step 4), the console either couldn't auto-add a permission at all (the qualifier is a
`${…}` placeholder, not a real alias) or covered only the bare function — never each alias.

**Fix:** add an invoke permission for *every* alias the stage variable can resolve to
(`live`, `canary`, `blue`, `green`):

```bash
REGION=us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
API_ID=<your-api-id>
aws lambda add-permission --function-name quotes-api --qualifier live \
  --statement-id apigw-invoke-live --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" --region $REGION
```

---

### `400 BadRequestException` — `1 validation error detected: Value 'arn:aws:lambda:…:function:quotes-api:' at 'functionName' failed to satisfy constraint`

The tell-tale detail is the **bare trailing colon** in that ARN: `…:function:quotes-api:` with
nothing after it.

**Cause:** the stage variable in the integration URI resolved to an **empty string**, so
API Gateway sent Lambda a qualifier-less-but-colon-terminated ARN, and Lambda rejected it on
regex validation *before your function was ever invoked*. The variable resolves to empty in
exactly three situations:

| Situation | What went wrong |
|---|---|
| Name **case** mismatch | The URI says `${stageVariables.lambdaAlias}` but the variable is defined as `lambdaalias` (or vice-versa). Stage variable names are **case-sensitive** and there is no fallback. |
| Variable **not set** on the stage | The URI references `lambdaAlias`, but the `prod` stage has no such variable (e.g. a stage created without `--variables`). |
| Tested from the **console Test tab** | The Test tab invokes the method *outside any stage* (see the log line `"stage":"test-invoke-stage"`), so **no** stage variables exist unless you type them into the Test panel yourself. |

**Diagnose:** the execution log tells you which one, in two lines. Look at the
`Endpoint request body after transformations` line for what API Gateway actually resolved:

```
"stageVariables":{"lambdaalias":"live"}      ← the name that was supplied
```

and the `Endpoint request URI` line for the result:

```
.../function:quotes-api:/invocations         ← empty  →  broken
.../function:quotes-api:live/invocations     ← resolved  →  correct
```

If the key in `stageVariables` doesn't character-for-character match the name inside
`${stageVariables.…}` in your URI, that's your bug.

**Fix:**

1. **Check the URI's spelling** against the stage's variable — both must be `lambdaAlias`:

   ```bash
   REGION=us-east-1
   API_ID=<your-api-id>

   aws apigateway get-integration --rest-api-id $API_ID \
     --resource-id <RESOURCE_ID> --http-method GET --region $REGION --query uri --output text
   aws apigateway get-stage --rest-api-id $API_ID --stage-name prod \
     --region $REGION --query variables
   ```

2. **If you're using the console Test tab**, fill in its **Stage variables** row — name
   `lambdaAlias`, value `live` — with no `=` and no spaces (they're separate name/value boxes).
   Leaving it blank *always* produces this error, even when `prod` is perfectly configured.
   The CLI equivalent, useful for confirming it from a terminal:

   ```bash
   aws apigateway test-invoke-method --rest-api-id $API_ID --resource-id <RESOURCE_ID> \
     --http-method GET --path-with-query-string /version \
     --stage-variables lambdaAlias=live --region $REGION
   ```

   Drop `--stage-variables` from that command and you reproduce the 400 on demand.

3. **If the stage is missing the variable**, add it (no redeploy needed):

   ```bash
   aws apigateway update-stage --rest-api-id $API_ID --stage-name prod --region $REGION \
     --patch-operations op=replace,path=/variables/lambdaAlias,value=live
   ```

> **`400` vs `500` — read the status code first.** A `400` with this validation message means
> the variable never resolved (spelling / missing / no stage). A `500 Internal server error`
> means it resolved fine but API Gateway lacks **invoke permission** on the alias it resolved to
> (previous entry). They look similar in the console and have completely different fixes.

---

### Changes to the API don't show up at the invoke URL

**Cause:** You edited resources/methods/integrations but didn't **redeploy**. A REST API only
serves what's in the deployment attached to the stage.

**Fix:** **Deploy API → select the `prod` stage → Deploy**. (Stage *variable* changes take
effect immediately and do **not** need a redeploy — only structural changes do.)

> **Give a redeploy ~1–2 minutes to propagate.** A `curl` fired seconds after
> `create-deployment` can still be served by the *previous* deployment — long enough to make you
> think a fix didn't work (or that a deliberate break "passed"). If a change seems not to have
> landed, wait and re-run the request before changing anything else. Redeploying an existing
> stage without `--variables` keeps its stage variables intact, so you don't need to re-pass them
> each time.

---

### `{"message":"Missing Authentication Token"}`

**Cause:** Despite the wording, this is **almost never about auth.** It's API Gateway's
generic "**no matching route** for this method + path on the deployed stage." The request
reached API Gateway but didn't match any resource/method. Common triggers:

- **Stage name missing from the URL** — e.g. calling `.../quotes` instead of `.../prod/quotes`.
- **Hitting the bare stage root** — `.../prod` with no resource path. The root `/` has no
  method, so it returns this error.
- **Not deployed / not redeployed** — the resource or method exists in the console but wasn't
  deployed to `prod`, so the stage doesn't serve it.
- **Wrong HTTP method** — e.g. `POST` to a path that only defines `GET`, or `GET /version`
  when the `/version` resource/method was never created.
- **Path typo or trailing slash** mismatch.

**Fix:** First, list what's actually deployed and compare against the URL you're calling:

```bash
REGION=us-east-1
API_ID=<your-api-id>

# Every resource path + the methods defined on it:
aws apigateway get-resources --rest-api-id $API_ID --region $REGION \
  --query 'items[].{path:path,methods:keys(resourceMethods)}' --output table

# Confirm the prod stage exists and has a deployment:
aws apigateway get-stages --rest-api-id $API_ID --region $REGION \
  --query 'item[].{stage:stageName,deployment:deploymentId}' --output table
```

- Path **not listed** → wrong path, or create the resource/method and **redeploy**.
- Path listed but **missing your verb** → add/deploy that method.
- Looks right but stage is missing or `deploymentId` is stale → **Deploy API → prod** again.

Then call the full URL: `https://<id>.execute-api.us-east-1.amazonaws.com/prod/quotes`.

> This is a *routing* error — distinct from `500 Internal server error`, which is the Lambda
> **alias-permission** issue above. A `403` here means routing; a `500` means the route matched
> but invoking the alias failed.

---

### `/version` always returns the old version during a rolling deploy

**Cause:** Either the weight is very low (10% means ~1 in 10 requests) or you published the
version *before* the env-var update landed.

**Fix:** Loop the probe (`for i in $(seq 1 30)`) to see the split. If v2 *never* appears,
re-check that `publish-version` ran **after** `update-function-configuration` finished — use
`aws lambda wait function-updated` between them, then publish again.

---

### `/version` (or any route) **always** returns the new version, ignoring the weighted alias

**Cause:** That method's integration invokes the **unqualified function** ARN
(`…:function:quotes-api`) instead of the alias ARN
(`…:function:quotes-api:${stageVariables.lambdaAlias}`). The unqualified ARN runs **`$LATEST`**,
and `$LATEST` carries the env var you set during the deploy (`APP_VERSION=2.0.0`). So that route
bypasses the `live` alias and its `AdditionalVersionWeights` entirely — 100% new version, every
request — while other routes that *do* target the alias still show the weighted split. (Classic
tell: `GET /quotes` returns `1.0.0` but `GET /version` returns `2.0.0`.) Easy to introduce by
wiring up a method (often added later, like `/version` or `/quotes/random`) without the
stage-variable qualifier.

**Fix:** Repoint **every** method's integration at the alias, then redeploy. Check what each one
targets:

```bash
REGION=us-east-1
API_ID=<your-api-id>
for RID in $(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[].id' --output text); do
  for M in GET POST; do
    aws apigateway get-integration --rest-api-id $API_ID --resource-id $RID --http-method $M \
      --region $REGION --query 'uri' --output text 2>/dev/null
  done
done
# A correct URI ends in  :quotes-api:${stageVariables.lambdaAlias}/invocations
# A broken one ends in    :quotes-api/invocations   (= $LATEST)
```

Patch each broken method (the `${…}` braces break CLI shorthand, so pass JSON via a file):

```bash
cat > /tmp/patch.json <<'EOF'
[{"op":"replace","path":"/uri","value":"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:quotes-api:${stageVariables.lambdaAlias}/invocations"}]
EOF
aws apigateway update-integration --rest-api-id $API_ID --resource-id <RID> \
  --http-method <GET|POST> --region $REGION --patch-operations file:///tmp/patch.json
# then redeploy so the change goes live:
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod --region $REGION
```

> Confirm with a large sample — `for i in $(seq 1 200)`. At low request volume Lambda applies
> weighted routing at **execution-environment** granularity, so a 60-request probe can read
> wildly off the configured weight; it converges to ~90/10 as volume grows.

---

### Canary tab: "promote" did nothing visible

**Cause:** Promote copies the **canary stage variable overrides** into the base stage, but if
your base alias (`live`) still points at v1, you also need to move that alias — or the base was
already pointing where the canary did.

**Fix:** After promoting, confirm `live` points at the new version
(`aws lambda get-alias --function-name quotes-api --name live`) and that `canarySettings` is
removed from the stage.

---

### `ResourceConflictException: Alias already exists`

**Cause:** Re-running a `create-alias` from an earlier attempt.

**Fix:** Use `update-alias` instead, or delete it first:
`aws lambda delete-alias --function-name quotes-api --name <alias>`.

---

### Proxy integration returns the body as a string with escaped quotes

**Cause:** Your handler returned a dict for `body` instead of a JSON **string**. With proxy
integration, `body` must be a string.

**Fix:** `json.dumps(...)` the body (as `_response()` in `app.py` already does).

---

### POST returns 400 "body must be valid JSON" even though you sent JSON

**Cause:** `curl` sent form-encoding, or you sent no `Content-Type`. The handler parses
`event["body"]` as JSON.

**Fix:** Send a JSON string: `curl -X POST $API/quotes -H 'Content-Type: application/json' -d '{"text":"hi"}'`.
