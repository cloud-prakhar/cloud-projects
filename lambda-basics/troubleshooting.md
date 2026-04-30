# Troubleshooting — Lambda Basics

A reference for every error you're likely to hit during Project 1.

---

## Error: "Unable to import module 'hello_world': No module named 'hello_world'"

**Symptom:** Invocation returns a `Runtime.ImportModuleError`.

**Cause:** The handler file is not at the **root** of the ZIP. When you zip `src/hello_world.py` without stripping the path, the archive contains `src/hello_world.py` — Lambda looks for `hello_world.py` at the root and can't find it.

**Fix:**

```bash
# Wrong — file lands at src/hello_world.py inside the ZIP
zip hello_world.zip src/hello_world.py

# Correct — -j strips all directory prefixes
zip -j hello_world.zip src/hello_world.py
```

---

## Error: "The role defined for the function cannot be assumed by Lambda"

**Symptom:** `aws lambda create-function` fails, or the function's State is `Failed` with the above message.

**Cause:** The IAM role's trust policy does not allow `lambda.amazonaws.com` to assume it. This happens when you create a role with the wrong trusted entity (e.g., EC2 instead of Lambda).

**Fix:** Verify the trust policy:

```bash
aws iam get-role \
  --role-name LambdaBasicsExecutionRole \
  --query 'Role.AssumeRolePolicyDocument'
```

It must contain:

```json
{
  "Effect": "Allow",
  "Principal": { "Service": "lambda.amazonaws.com" },
  "Action": "sts:AssumeRole"
}
```

If the principal is wrong, update the trust policy:

```bash
aws iam update-assume-role-policy \
  --role-name LambdaBasicsExecutionRole \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":{"Service":"lambda.amazonaws.com"},
      "Action":"sts:AssumeRole"
    }]
  }'
```

---

## Error: "Task timed out after X seconds"

**Symptom:** The REPORT line shows `Duration: 10000.00 ms` (or whatever your timeout is) and the function exits with a timeout error.

**Cause:** Your function is running longer than the configured timeout. For Hello World this should never happen, but if you add a blocking call (e.g., a misconfigured HTTP request) it can.

**Fix:** 

1. Check your handler for any blocking I/O (network calls, `time.sleep()`).
2. If the function legitimately needs more time, increase the timeout:

```bash
aws lambda update-function-configuration \
  --function-name HelloWorldLambda \
  --timeout 30
```

Maximum timeout is 15 minutes (900 seconds).

---

## Error: Invoke returns HTTP 200 but the payload has `"FunctionError": "Unhandled"`

**Symptom:** `aws lambda invoke` exits cleanly with status 200, but `cat response.json` shows an error stack trace rather than your expected output.

**Cause:** Lambda invocation itself succeeded (the function was reached), but the function code threw an unhandled exception. The invocation HTTP code is 200 regardless of whether your code crashed.

**Fix:** Always check `response["FunctionError"]` in Boto3 or look at the response file after CLI invocations. In CloudWatch Logs, look for lines tagged `[ERROR]`.

---

## Error: No logs appear in CloudWatch

**Symptom:** You can invoke the function, but the log group `/aws/lambda/HelloWorldLambda` doesn't exist or has no events.

**Cause:** The execution role is missing CloudWatch Logs permissions.

**Fix:** Verify `AWSLambdaBasicExecutionRole` is attached:

```bash
aws iam list-attached-role-policies \
  --role-name LambdaBasicsExecutionRole \
  --query 'AttachedPolicies[*].PolicyName'
```

If it's missing:

```bash
aws iam attach-role-policy \
  --role-name LambdaBasicsExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

---

## Error: `ResourceNotFoundException` when invoking via CLI

**Symptom:** `An error occurred (ResourceNotFoundException) when calling the Invoke operation: Function not found: arn:aws:lambda:...`

**Cause:** The function name is wrong or you're in the wrong region.

**Fix:** Always pass `--region` explicitly or check your default region:

```bash
aws configure get region

aws lambda list-functions --region us-east-1 \
  --query 'Functions[*].FunctionName'
```

---

## Error: Environment variable not read — function sees old value

**Symptom:** You updated an environment variable but the function still returns the old value.

**Cause:** The Lambda container was already warm with the old variable loaded at module level. Because you read env vars outside the handler (at module load time), changes require a new container.

**Fix:** Force a cold start by doing a dummy configuration update:

```bash
aws lambda update-function-configuration \
  --function-name HelloWorldLambda \
  --description "$(date) — force cold start"
```

Or simply wait; Lambda scales down idle containers after a few minutes of inactivity.

---

## General debugging checklist

1. Check the CloudWatch log stream for `[ERROR]` lines
2. Verify the IAM role ARN attached to the function
3. Confirm the ZIP structure with `unzip -l your_file.zip`
4. Confirm the handler string matches `<filename_without_py>.<function_name>`
5. Check the function's State — it must be `Active`, not `Pending` or `Failed`
