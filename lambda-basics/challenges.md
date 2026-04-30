# Challenges — Lambda Basics

Completed the main project? Try these challenges to deepen your understanding. They use only the services introduced in this project.

---

## Challenge 1 — Structured Logging

**Goal:** Replace plain `logger.info()` strings with JSON-structured log lines.

Instead of:
```
INFO Event received: {"name": "Alice"}
```

Output:
```json
{"level": "INFO", "request_id": "abc123", "message": "Event received", "name": "Alice"}
```

**Why it matters:** JSON logs are machine-parseable. CloudWatch Log Insights can query individual JSON fields — you can write `filter name = "Alice"` instead of `filter @message like /Alice/`.

**Hint:** Use Python's `json.dumps()` and include `context.aws_request_id` in every log line.

---

## Challenge 2 — Error Handling and Custom Error Response

**Goal:** Wrap your handler in a try/except block. If an unexpected error occurs, return a structured error response instead of letting Lambda surface an `Unhandled` error.

```json
{
  "statusCode": 500,
  "body": "{\"error\": \"InternalError\", \"message\": \"Something went wrong\", \"request_id\": \"abc123\"}"
}
```

**Bonus:** Add a specific branch that returns HTTP 400 when the `name` field is an integer instead of a string.

---

## Challenge 3 — Invocation via AWS SDK

**Goal:** Modify `test_invoke.py` to:

1. Invoke the function **asynchronously** (InvocationType = `Event`)
2. Poll CloudWatch Logs until you see the log line from that specific invocation (hint: filter by `aws_request_id`)
3. Print the log line to stdout

This simulates fire-and-forget invocation patterns common in event-driven systems.

---

## Challenge 4 — Function Aliases and Versions

**Goal:**

1. Publish version `1` of `HelloWorldLambda` (Console: **Actions → Publish new version**)
2. Create an alias `live` pointing to version `1`
3. Deploy a slightly different handler (change the greeting text) and publish version `2`
4. Update the alias to point to version `2`
5. Use the CLI to invoke via the alias: `--function-name HelloWorldLambda:live`

**Why it matters:** Aliases decouple the "name callers use" from the "version deployed." Blue/green Lambda deployments and canary releases use this pattern.

---

## Challenge 5 — Reserved Concurrency

**Goal:**

1. Set the reserved concurrency of `HelloWorldLambda` to `1`
2. Write a script that fires 5 simultaneous async invocations
3. Observe in CloudWatch Logs how many actually ran concurrently vs. were throttled (look for `TooManyRequestsException` in the response or `Throttled` in the REPORT line)
4. Remove the concurrency cap

**Hint:** Use Python's `concurrent.futures.ThreadPoolExecutor` to fire all 5 invocations in parallel.
