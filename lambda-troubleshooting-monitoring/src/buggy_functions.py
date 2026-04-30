"""
Lambda Troubleshooting & Monitoring — Project 4
A set of intentionally broken handlers that demonstrate common Lambda failure
modes. Deploy each as a separate function (or use the 'scenario' event key
to route to the right one from a single function).

Invoke with: {"scenario": "<name>"}
"""

import json
import logging
import os
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    scenario = event.get("scenario", "ok")
    logger.info("Running scenario: %s | request_id: %s", scenario, context.aws_request_id)

    scenarios = {
        "ok":              _scenario_ok,
        "unhandled_error": _scenario_unhandled_error,
        "timeout":         _scenario_timeout,
        "memory_oom":      _scenario_memory_oom,
        "missing_env":     _scenario_missing_env_var,
        "bad_json":        _scenario_bad_json_response,
        "divide_by_zero":  _scenario_divide_by_zero,
        "partial_success": _scenario_partial_success,
    }

    fn = scenarios.get(scenario)
    if fn is None:
        return {"statusCode": 400, "body": f"Unknown scenario: {scenario}. Valid: {list(scenarios.keys())}"}

    return fn(event, context)


def _scenario_ok(event, context):
    return {"statusCode": 200, "body": json.dumps({"message": "All good!"})}


def _scenario_unhandled_error(event, context):
    # This raises an unhandled exception.
    # In CloudWatch you'll see an [ERROR] line with the full traceback.
    # The function's ErrorCount metric increments.
    raise ValueError("Something went wrong — this is intentional for learning.")


def _scenario_timeout(event, context):
    # Sleeps longer than the configured timeout.
    # In CloudWatch you'll see: "Task timed out after X.XX seconds"
    # The REPORT line will show Duration == Timeout (the function was killed).
    logger.warning("About to sleep longer than timeout — expecting a timeout error")
    remaining_ms = context.get_remaining_time_in_millis()
    logger.info("Time remaining before sleep: %d ms", remaining_ms)
    time.sleep(60)  # Set function timeout to < 60s to see this trigger


def _scenario_memory_oom(event, context):
    # Allocates memory until Lambda kills the container.
    # You'll see "Runtime exited with error: signal: killed" in CloudWatch.
    # The Max Memory Used metric will equal the Memory Size limit.
    logger.warning("Allocating memory until OOM — this will kill the container")
    data = []
    while True:
        data.append("x" * 10_000_000)  # 10 MB per iteration


def _scenario_missing_env_var(event, context):
    # Attempts to read a required env var that doesn't exist.
    # Best practice: validate at startup, not deep in business logic.
    db_url = os.environ["DATABASE_URL"]  # KeyError if not set
    return {"statusCode": 200, "body": f"Connected to: {db_url}"}


def _scenario_bad_json_response(event, context):
    # Returns a non-serialisable object.
    # This causes a runtime serialisation error rather than an application error.
    import datetime
    return {"statusCode": 200, "timestamp": datetime.datetime.now()}  # not JSON serialisable


def _scenario_divide_by_zero(event, context):
    numerator = int(event.get("numerator", 10))
    denominator = int(event.get("denominator", 0))
    result = numerator / denominator  # ZeroDivisionError
    return {"statusCode": 200, "result": result}


def _scenario_partial_success(event, context):
    # Simulates batch processing where some items fail.
    # Returns a structured result with successes and failures — useful for
    # demonstrating how to report partial batch failures to SQS/Kinesis.
    items = event.get("items", ["item1", "item2", "bad-item", "item3"])
    successes, failures = [], []
    for item in items:
        if "bad" in item:
            failures.append({"item": item, "error": "Validation failed"})
            logger.error("Failed to process item: %s", item)
        else:
            successes.append(item)
            logger.info("Successfully processed: %s", item)

    return {
        "statusCode": 207 if failures else 200,
        "body": json.dumps({"successes": successes, "failures": failures}),
    }
