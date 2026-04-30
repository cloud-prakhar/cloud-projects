# Step 4 — Configure with Environment Variables

Hard-coding configuration values inside a Lambda function is an anti-pattern. Environment variables let you:

- Change behaviour between environments (dev / staging / prod) **without redeploying code**
- Keep ARNs, table names, and feature flags out of source code
- Manage configuration centrally (via console, CDK, Terraform, etc.)

---

## What you'll deploy

The `src/with_env_vars.py` handler reads three environment variables at **module load time** (outside the handler function). This means the values are read once during the cold start and reused for all subsequent warm invocations — efficient and clean.

```python
APP_ENV   = os.environ.get("APP_ENV", "dev")
TABLE_NAME = os.environ.get("TABLE_NAME", "")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
```

If `TABLE_NAME` is empty, the function raises `EnvironmentError`. This is intentional — fail loudly at startup rather than silently returning wrong data.

---

## Step A — Update the function code

### Package and update

```bash
cd /path/to/lambda-basics
zip -j with_env_vars.zip src/with_env_vars.py

aws lambda update-function-code \
  --function-name HelloWorldLambda \
  --zip-file fileb://with_env_vars.zip

# Wait for update to finish
aws lambda wait function-updated --function-name HelloWorldLambda
```

### Update the handler string

```bash
aws lambda update-function-configuration \
  --function-name HelloWorldLambda \
  --handler with_env_vars.handler
```

---

## Step B — Set environment variables

### Via Console

1. **Configuration → Environment variables → Edit**
2. Add three key-value pairs:

   | Key | Value |
   |-----|-------|
   | `APP_ENV` | `dev` |
   | `TABLE_NAME` | `users-dev` |
   | `MAX_RETRIES` | `3` |

3. Click **Save**.

### Via CLI

```bash
aws lambda update-function-configuration \
  --function-name HelloWorldLambda \
  --environment 'Variables={APP_ENV=dev,TABLE_NAME=users-dev,MAX_RETRIES=3}'
```

---

## Step C — Test it

```bash
aws lambda invoke \
  --function-name HelloWorldLambda \
  --cli-binary-format raw-in-base64-out \
  --payload '{}' \
  response.json

cat response.json
```

Expected:

```json
{
  "statusCode": 200,
  "body": "{\"environment\": \"dev\", \"table_name\": \"users-dev\", \"max_retries\": 3}"
}
```

### Test the failure path — omit TABLE_NAME

```bash
# Remove TABLE_NAME to trigger the EnvironmentError
aws lambda update-function-configuration \
  --function-name HelloWorldLambda \
  --environment 'Variables={APP_ENV=dev,MAX_RETRIES=3}'

aws lambda wait function-updated --function-name HelloWorldLambda

aws lambda invoke \
  --function-name HelloWorldLambda \
  --cli-binary-format raw-in-base64-out \
  --payload '{}' \
  response.json

cat response.json
```

The response payload will contain a `FunctionError` key with the exception details. The HTTP status of the invocation is still 200 — Lambda delivered your invocation — but the function itself errored.

In CloudWatch Logs you'll see:

```
[ERROR] EnvironmentError: TABLE_NAME environment variable is not set.
```

### Restore TABLE_NAME after testing

```bash
aws lambda update-function-configuration \
  --function-name HelloWorldLambda \
  --environment 'Variables={APP_ENV=dev,TABLE_NAME=users-dev,MAX_RETRIES=3}'
```

---

## Environment variable limits and best practices

| Rule | Reason |
|------|--------|
| Max total size: 4 KB (all vars combined) | AWS hard limit |
| Do not store raw secrets | They appear in plaintext in the console. Use Secrets Manager or SSM Parameter Store instead. |
| Store the **path** to a secret, not the secret itself | e.g. `SECRET_PATH=/prod/db/password` — fetch at runtime with `boto3.client('ssm')` |
| Prefix vars by environment | `DB_HOST_PROD`, `DB_HOST_DEV` — makes cross-env accidents obvious |

---

## Checkpoint

- [ ] Deployed `with_env_vars.py` and updated the handler
- [ ] Set `APP_ENV`, `TABLE_NAME`, `MAX_RETRIES` via console or CLI
- [ ] Invoked the function and saw the environment reflected in the response
- [ ] Deliberately removed `TABLE_NAME` and observed the error in CloudWatch Logs

---

**Next →** [05-cleanup.md](05-cleanup.md)
