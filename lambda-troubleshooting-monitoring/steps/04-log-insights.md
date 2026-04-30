# Step 4 — CloudWatch Log Insights Queries

CloudWatch Log Insights provides a SQL-like query language that runs across multiple log streams simultaneously. It's far more powerful than `filter-log-events` for aggregation, statistics, and cross-invocation analysis.

---

## Opening Log Insights

**Console:** CloudWatch → Log Insights → Select log group: `/aws/lambda/BuggyLambda`

Or query via CLI:

```bash
LOG_GROUP="/aws/lambda/BuggyLambda"
END=$(date +%s)
START=$((END - 3600))  # last 1 hour

run_query() {
  local QUERY="$1"
  QUERY_ID=$(aws logs start-query \
    --log-group-name "$LOG_GROUP" \
    --start-time "$START" \
    --end-time "$END" \
    --query-string "$QUERY" \
    --query 'queryId' --output text)

  while true; do
    STATUS=$(aws logs get-query-results --query-id "$QUERY_ID" --query 'status' --output text)
    [ "$STATUS" = "Complete" ] && break
    sleep 2
  done

  aws logs get-query-results --query-id "$QUERY_ID" --query 'results'
}
```

---

## Useful Log Insights Queries

### 1. Find all errors in the last hour

```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20
```

```bash
run_query 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20'
```

---

### 2. Count errors by error type

```sql
fields @message
| filter @message like /\[ERROR\]/
| parse @message "* *: *" as level, errorType, errorMessage
| stats count(*) as errorCount by errorType
| sort errorCount desc
```

---

### 3. Average and p99 duration across all invocations

Lambda REPORT lines are structured and parseable by Log Insights:

```sql
filter @type = "REPORT"
| stats avg(@duration) as avgDuration,
        percentile(@duration, 99) as p99Duration,
        max(@duration) as maxDuration,
        count(*) as invocationCount
```

---

### 4. Cold starts (Init Duration present)

```sql
filter @type = "REPORT"
| filter @initDuration > 0
| stats count(*) as coldStarts,
        avg(@initDuration) as avgInitDuration
```

---

### 5. Memory usage trend

```sql
filter @type = "REPORT"
| stats max(@maxMemoryUsed) as maxMemMB,
        avg(@maxMemoryUsed) as avgMemMB
  by bin(5m)
```

This shows memory usage over time in 5-minute buckets — useful for spotting memory leaks.

---

### 6. Find all invocations that timed out

```sql
fields @timestamp, @requestId, @duration
| filter @message like /Task timed out/
| sort @timestamp desc
```

---

### 7. Invocation volume over time

```sql
filter @type = "REPORT"
| stats count(*) as invocations by bin(5m)
| sort @timestamp asc
```

---

### 8. Error rate (errors / total invocations)

```sql
filter @type = "REPORT"
| stats count(*) as total by bin(1h)
| join (
    filter @message like /ERROR/
    | stats count(*) as errors by bin(1h)
  ) using @timestamp
| project @timestamp, errors, total, (errors / total * 100) as errorRate
```

---

### 9. Find the slowest invocations

```sql
filter @type = "REPORT"
| sort @duration desc
| fields @requestId, @duration, @billedDuration, @maxMemoryUsed
| limit 10
```

---

### 10. Search for a specific RequestId across all streams

```sql
fields @timestamp, @message
| filter @requestId = "YOUR-REQUEST-ID-HERE"
| sort @timestamp asc
```

---

## Log Insights for the BuggyLambda scenarios

After running the scenarios in Step 2, try these targeted queries:

```bash
# How many of each scenario ran?
run_query '
  fields @message
  | filter @message like /Running scenario/
  | parse @message "Running scenario: *" as scenario
  | stats count(*) by scenario
'

# All timeout events
run_query '
  fields @timestamp, @message
  | filter @message like /timed out/
  | sort @timestamp desc
'

# Memory-related kills
run_query '
  fields @timestamp, @message
  | filter @message like /signal: killed/
  | sort @timestamp desc
'
```

---

## Checkpoint

- [ ] Opened Log Insights via Console or CLI
- [ ] Ran the "find all errors" query and saw results from Step 2's scenarios
- [ ] Ran the "p99 duration" query and saw statistics
- [ ] Ran the "cold starts" query and identified cold-start invocations
- [ ] Found the timeout and OOM invocations using targeted queries

---

**Next →** [05-dead-letter-queue.md](05-dead-letter-queue.md)
