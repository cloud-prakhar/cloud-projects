# Troubleshooting Reference — Lambda Monitoring & Boto3

The definitive guide to diagnosing Lambda failures. Each section maps a symptom to a root cause and a fix.

---

## Quick Diagnostic Checklist

When a Lambda function misbehaves, work through this checklist before diving deeper:

1. **Check the function's State**
   ```bash
   aws lambda get-function --function-name <NAME> --query 'Configuration.State'
   ```
   Must be `Active`. `Pending` means deploying. `Failed` means a configuration problem.

2. **Check CloudWatch Logs for `[ERROR]`**
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/<NAME> \
     --start-time $(($(date +%s%3N) - 600000)) \
     --filter-pattern "[ERROR]" \
     --query 'events[*].message' --output text
   ```

3. **Check the REPORT line for timeout/OOM**
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/<NAME> \
     --start-time $(($(date +%s%3N) - 600000)) \
     --filter-pattern "REPORT" \
     --query 'events[*].message' --output text | tail -5
   ```

4. **Check the IAM role**
   ```bash
   aws lambda get-function-configuration \
     --function-name <NAME> \
     --query 'Role'
   ```

---

## Error Catalog

### 1. `Runtime.ImportModuleError: No module named '<module>'`

**Cause A:** Module is not in the standard library and no layer is attached.  
**Fix:** Attach the appropriate layer (see Lambda Layers project) or bundle the dependency in the function ZIP.

**Cause B:** The ZIP structure is wrong — file is nested inside a subdirectory.  
**Fix:** Use `zip -j` to strip directory prefixes.

**Cause C:** The handler string points to the wrong file.  
**Fix:** Handler string format is `<filename_without_py>.<function_name>`. If the file is `boto3_ec2.py` and the function is `handler`, the handler string is `boto3_ec2.handler`.

---

### 2. `Task timed out after X.XX seconds`

**Symptom in CloudWatch:**
```
2026-04-30T... Task timed out after 10.00 seconds
```

**Causes and fixes:**

| Cause | Fix |
|-------|-----|
| Network call to external service is slow | Increase timeout; add connection/read timeouts to requests |
| Synchronous wait on a downstream service | Use async patterns; increase timeout |
| Infinite loop in business logic | Fix the logic; add a guard counter |
| Cold start + function work exceeds timeout | Increase timeout; increase memory (more CPU) |

```bash
# Increase timeout to 60 seconds
aws lambda update-function-configuration \
  --function-name <NAME> \
  --timeout 60
```

---

### 3. `Runtime exited with error: signal: killed` (OOM)

**Symptom:** Max Memory Used equals Memory Size in the REPORT line:
```
REPORT ... Memory Size: 128 MB  Max Memory Used: 128 MB
```

**Fix:** Increase memory allocation:
```bash
aws lambda update-function-configuration \
  --function-name <NAME> \
  --memory-size 512
```

**Also investigate:** Memory leak in the function code. Look for unbounded data accumulation across warm invocations — global variables that grow with each invocation are a common cause.

---

### 4. `AccessDeniedException` / `is not authorized to perform`

**Symptom in CloudWatch:**
```
[ERROR] ClientError: An error occurred (AccessDenied) when calling the PutObject operation: 
Access Denied
```

**Diagnosis:**
```bash
# Show all policies on the execution role
ROLE=$(aws lambda get-function-configuration \
  --function-name <NAME> --query 'Role' --output text | sed 's|.*role/||')

aws iam list-role-policies --role-name "$ROLE" --query 'PolicyNames'
aws iam list-attached-role-policies --role-name "$ROLE" --query 'AttachedPolicies[*].PolicyName'
```

**Fix:** Add the required permission to the role's inline policy. The error message tells you exactly which action and resource are denied.

---

### 5. `FunctionError: Unhandled` but HTTP status is 200

**Explanation:** Lambda returns HTTP 200 for *invocation delivery success*, not function success. A `FunctionError` key in the response indicates the function itself raised an unhandled exception.

**Fix:** Check the response payload for `errorType` and `errorMessage`, and the CloudWatch log for the full traceback.

```python
# In Boto3: always check for FunctionError
response = lambda_client.invoke(FunctionName=fn, Payload=payload)
if response.get("FunctionError"):
    body = json.loads(response["Payload"].read())
    raise RuntimeError(f"Lambda error: {body['errorType']}: {body['errorMessage']}")
```

---

### 6. No logs in CloudWatch at all

**Cause A:** The execution role is missing CloudWatch Logs permissions.  
**Fix:**
```bash
aws iam attach-role-policy \
  --role-name <ROLE_NAME> \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

**Cause B:** The function was never actually invoked (trigger not configured correctly).  
**Fix:** Try a manual invocation:
```bash
aws lambda invoke --function-name <NAME> --payload '{}' /tmp/resp.json && cat /tmp/resp.json
```
If this works, the trigger configuration is the problem. If this also produces no logs, it's the IAM role.

---

### 7. Environment variable not picked up

**Cause:** Read at module load time (outside the handler) but the container was warm when the variable was updated.  
**Fix:** Force a cold start by changing the function description or any config value, or wait for existing containers to idle out.

---

### 8. SQS `QueueDoesNotExist`

**Symptom:** Lambda's SQS calls fail with `QueueDoesNotExist`.  
**Cause:** Wrong queue name or wrong region.  
**Fix:** Always use `get_queue_url(QueueName=...)` to resolve the URL rather than constructing it manually. Check the region matches.

---

### 9. EC2 `UnauthorizedOperation`

**Symptom:** Lambda cannot stop/start EC2 instances despite the IAM policy listing those actions.  
**Cause:** The instance may be in a different region than the Lambda function, or the instance has a `deny` policy from AWS Organizations SCPs.  
**Fix:** Verify the region:
```bash
aws ec2 describe-instances --instance-ids i-0abc123 --region us-east-1
```
If the instance is in a different region, pass the region explicitly to the Boto3 client.

---

### 10. Pre-signed S3 URL returns `403 Forbidden`

**Causes and fixes:**

| Cause | Fix |
|-------|-----|
| URL has expired | Generate a new one with a longer `ExpiresIn` |
| Object does not exist | Verify the key in S3 |
| Bucket has a policy that denies GetObject | Check the bucket policy in the S3 console |
| VPC endpoint policy is blocking | Rare; check if the URL is being accessed from inside a VPC |

---

### 11. DLQ is not receiving failed async invocations

**Cause A:** The function was invoked **synchronously** (RequestResponse). DLQs only apply to **async** invocations (Event, SNS, S3, etc.).  
**Fix:** Use `--invocation-type Event` for async invocations.

**Cause B:** Lambda's execution role lacks `sqs:SendMessage` on the DLQ.  
**Fix:** Add the permission (see Step 5 of this project).

**Cause C:** The function succeeded despite appearing to fail (the error was caught internally).  
**Fix:** Ensure the function raises an unhandled exception or returns a non-success response for Lambda's retry logic to trigger.

---

## Log Insights Quick Reference

```sql
-- All errors in the last hour
filter @message like /ERROR/
| sort @timestamp desc | limit 50

-- P99 invocation duration
filter @type = "REPORT"
| stats percentile(@duration, 99) as p99, count(*) as total

-- Cold starts only
filter @type = "REPORT" and @initDuration > 0
| stats count(*) as coldStarts, avg(@initDuration) as avgInitMs

-- Find by RequestId
filter @requestId = "YOUR-ID"
| sort @timestamp asc

-- Memory trend (5-min buckets)
filter @type = "REPORT"
| stats avg(@maxMemoryUsed) as avgMem by bin(5m)

-- Error rate per 5 minutes
filter @type = "REPORT" or @message like /ERROR/
| stats
    sum(@type = "REPORT") as invocations,
    sum(@message like /ERROR/) as errors
  by bin(5m)
```
