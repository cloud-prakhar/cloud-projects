# Step 4 — Deploy to a Stage (and Point It at an Alias)

Here's the thing newcomers trip on: **building the API doesn't make it live.** A REST API
goes public only when you create a **deployment** (a snapshot of the API config) and assign
it to a **stage** (a named, addressable copy — `dev`, `prod`, …). Change the API? You must
**redeploy** for the change to appear.

We'll also do one forward-looking thing now that makes every later deployment step easy: wire
the stage's Lambda integration to an **alias** through a **stage variable**, instead of
hardwiring it to the function. That single indirection is what makes rolling, canary, and
blue-green possible without ever editing the API again.

---

## 4.1 Publish the Lambda: Version 1 + the `live` Alias

A Lambda **version** is an immutable snapshot of code+config; `$LATEST` is the mutable draft.
An **alias** is a named pointer to a version (think: a git branch pointing at a commit). The
API will call the *alias*, so we can move the pointer later without touching API Gateway.

```bash
REGION=us-east-1

# Publish the current code as immutable version 1
aws lambda publish-version --function-name quotes-api --region $REGION \
  --query 'Version' --output text          # prints: 1

# Create alias "live" pointing at version 1
aws lambda create-alias --function-name quotes-api \
  --name live --function-version 1 --region $REGION
```

Console equivalent: **Lambda → quotes-api → Versions → Publish new version**, then
**Aliases → Create alias** → name `live`, version `1`.

---

## 4.2 Point the Integration at the Alias via a Stage Variable

We want the integration URI to read the alias name from a **stage variable** named
`lambdaAlias`. That way `prod` can say `lambdaAlias = live` and a canary can override it.

For **each** method you created (GET/POST `/quotes`, GET `/quotes/{id}`, GET `/version`):

1. Select the method → **Integration request** → **Edit**.
2. Leave **Integration type** = *Lambda function* and keep **Lambda proxy integration** *on*.
3. In the **Lambda function** box, type the **full function ARN** with the stage variable as
   the qualifier (alias). The box is a typeahead — it will *not* offer a dropdown match for a
   value containing `${…}`, and that's expected. Ignore the "no results" hint and just leave
   your typed text in place, then **Save**.

   Use the ARN form (replace `<ACCOUNT_ID>` with your 12-digit account number):

   ```
   arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:quotes-api:${stageVariables.lambdaAlias}
   ```

   Why the full ARN and not just `quotes-api:${stageVariables.lambdaAlias}`? The short
   `name:qualifier` form is what the *old* console accepted. The current console resolves the
   field by ARN, so a bare name plus a stage-variable qualifier often fails to save or silently
   drops the qualifier. The full ARN always works. Concretely, with account `123456789012`:

   ```
   arn:aws:lambda:us-east-1:123456789012:function:quotes-api:${stageVariables.lambdaAlias}
   ```

   > **The variable name is case-sensitive — and it is the #1 typo in this step.**
   > `${stageVariables.lambdaAlias}` in the URI and `lambdaAlias` on the stage must match
   > character for character. `lambdaalias` does **not** resolve to `lambdaAlias`; the
   > reference silently becomes an empty string and the request fails with a `400` complaining
   > that `arn:...:function:quotes-api:` (note the bare trailing colon) doesn't match Lambda's
   > `functionName` pattern. Pick the spelling once and use it in the URI, on every stage, and
   > in the console Test panel.

4. When you save, the console pops a **"Add permission to Lambda function"** dialog. It can
   only add permission for the *literal* text — which contains `${stageVariables.lambdaAlias}`,
   not a real alias — so click **Cancel** (or let it fail). You'll grant the real permission
   explicitly in the CLI block below.

**CLI alternative** (sets the integration URI directly — handy if the console fights you).
The integration URI is the Lambda ARN *embedded inside* an API Gateway invocation path, and
the embedded ARN carries the stage variable:

```bash
REGION=us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
API_ID=<your-api-id>

URI="arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:quotes-api:\${stageVariables.lambdaAlias}/invocations"

# Run for EACH method+resource. Example: GET on the /version resource.
# Get RESOURCE_ID from: aws apigateway get-resources --rest-api-id $API_ID --region $REGION
aws apigateway put-integration \
  --rest-api-id $API_ID --resource-id <RESOURCE_ID> --http-method GET \
  --type AWS_PROXY --integration-http-method POST \
  --uri "$URI" --region $REGION
```

> Note the `\${stageVariables...}` — the backslash stops *your shell* from expanding it, so
> the literal `${stageVariables.lambdaAlias}` reaches API Gateway, which substitutes it at
> request time.

Because the function name now contains a stage variable, you must grant API Gateway
permission to invoke the **alias** explicitly (the console's auto-permission only covered the
bare function):

```bash
REGION=us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
API_ID=<your-api-id>

aws lambda add-permission --function-name quotes-api \
  --qualifier live \
  --statement-id apigw-invoke-live --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" --region $REGION
```

> You'll add one more `add-permission` for each *new* alias you introduce in later steps
> (e.g. `canary`, `green`). API Gateway can only invoke an alias it has explicit permission
> for. This is the #1 cause of `500 Internal server error` in this project — see
> [troubleshooting.md](../troubleshooting.md).

---

## 4.3 Create the `prod` Deployment + Stage

**Console:**

1. **Deploy API** (top right).
2. **Stage:** *New stage* → **Stage name:** `prod` → **Deploy**.
3. On the stage page, open **Stage variables → Add** → `lambdaAlias = live` → Save.
4. Copy the **Invoke URL** at the top (e.g. `https://abc123.execute-api.us-east-1.amazonaws.com/prod`).

**CLI:**

```bash
aws apigateway create-deployment --rest-api-id $API_ID \
  --stage-name prod --variables lambdaAlias=live --region $REGION
```

---

## 4.4 Test the Live API

Set `API` to **your** invoke URL (from 4.3 — it must end in `/prod`, with no trailing slash):

```bash
API=https://abc123.execute-api.us-east-1.amazonaws.com/prod   # <-- replace with yours

curl $API/quotes ; echo            # the two quotes, "version":"1.0.0"
curl $API/quotes/1 ; echo          # one quote
curl "$API/version" ; echo         # {"version":"1.0.0"}

# POST — send JSON and SAY it's JSON. -d alone sends form-encoding.
curl -X POST "$API/quotes" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Make it work, then make it right.","author":"Kent Beck"}' ; echo
```

Two things that make these reliable:

- **No `-s`.** Silent mode swallows TLS/connection errors *and* HTTP error bodies, so a failed
  request looks like "nothing happened." Run them loud while testing; add `-s` only once
  they're known-good.
- **`; echo`** prints a newline after each response. The handler returns JSON with no trailing
  `\n`, so without this the body merges into your next shell prompt and looks empty.

`GET /version` returning `1.0.0` confirms the stage → variable → `live` alias → version 1
chain works end to end. Keep that command handy — it's your "which version is serving?"
probe for the next three steps.

### Don't use the console **Test** button from here on

Step 3.3 had you test a method with the console's **Test** tab. That stops being a valid smoke
test the moment the integration URI contains a stage variable — and it's worth understanding
why, because the failure looks like a broken API.

The Test tab invokes the method **outside any stage**. You can see it in the execution log it
prints: `"stage":"test-invoke-stage"`, a synthetic stage that exists only for that call. No
stage means no stage variables, so `${stageVariables.lambdaAlias}` resolves to nothing and you
get:

```
Endpoint request URI: .../function:quotes-api:/invocations     ← empty qualifier
Status: 400   "1 validation error detected: Value 'arn:aws:lambda:...:function:quotes-api:'
               at 'functionName' failed to satisfy constraint: ..."
```

Your API is fine; the test harness just isn't carrying the variable. Two ways forward:

- **Preferred — test through the stage:** `curl "$API/version"`. This exercises the real path
  (stage → variable → alias → version), which is exactly what Steps 5–7 change.
- **If you want the Test tab anyway:** fill in its **Stage variables** row first — name
  `lambdaAlias`, value `live`. They're separate name/value boxes: no `=`, no spaces, and the
  name must match the case in your URI. The same call from the CLI:

  ```bash
  aws apigateway test-invoke-method --rest-api-id $API_ID --resource-id <RESOURCE_ID> \
    --http-method GET --path-with-query-string /version \
    --stage-variables lambdaAlias=live --region $REGION
  ```

Either way, confirm the fix in the log: the `Endpoint request URI` line should read
`.../function:quotes-api:live/invocations`, with the alias filled in.

### If a command prints nothing or an error

Make the status code visible — this turns a silent failure into a diagnosis:

```bash
curl -i "$API/version"             # -i shows the HTTP status line + headers
```

| What you see | Meaning | Fix |
|---|---|---|
| `{"message":"Missing Authentication Token"}` / `403` | Path or stage wrong — no route matched | Confirm the URL ends `/prod` **and** has the resource (`/version`, `/quotes`). See [troubleshooting.md](../troubleshooting.md). |
| `{"message":"Internal server error"}` / `500` | Route matched but invoking the alias failed | Add the `live` alias invoke permission (4.2). |
| `1 validation error detected: ...'functionName'` / `400` | The stage variable resolved to **empty** — misspelled/miscased name, variable missing from the stage, or you used the console **Test** tab | Match the case exactly (`lambdaAlias`), or supply the variable in the Test panel. See above and [troubleshooting.md](../troubleshooting.md). |
| `curl: (6) Could not resolve host` | `API` unset or has a typo | Re-check the `API=` line; it must be one line, no spaces around `=`. |
| Totally empty, exit code 0 | You used `-s` and hit an error | Drop `-s`, or add `-i` as above. |

---

## Checkpoint

- [ ] Lambda **version 1** is published and alias **`live`** points to it
- [ ] Every method's integration URI ends with `...:function:quotes-api:${stageVariables.lambdaAlias}` (full ARN form)
- [ ] API Gateway has `lambda:InvokeFunction` permission on the **`live`** alias
- [ ] Stage **`prod`** exists with stage variable `lambdaAlias=live`
- [ ] `curl $API/version` returns `{"version":"1.0.0"}`
- [ ] You know why the console **Test** tab returns `400` here, and how to feed it the stage variable

---

**Next:** [Step 5 — Rolling Deployment](./05-rolling-deployment.md)
