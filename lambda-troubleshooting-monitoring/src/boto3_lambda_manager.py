"""
Lambda Troubleshooting & Monitoring — Project 4
Boto3 automation: Lambda self-management and log querying.

This script runs LOCALLY (not as a Lambda handler) to:
  1. Fetch the last N log events from any Lambda function
  2. Run a CloudWatch Log Insights query against a log group
  3. Report function memory and error metrics from CloudWatch Metrics

Usage:
    python src/boto3_lambda_manager.py --function BuggyLambda --scenario unhandled_error
    python src/boto3_lambda_manager.py --function BuggyLambda --logs
    python src/boto3_lambda_manager.py --function BuggyLambda --insights "filter @message like /ERROR/"
    python src/boto3_lambda_manager.py --function BuggyLambda --metrics
"""

import argparse
import json
import time
from datetime import datetime, timedelta, timezone

import boto3

REGION = "us-east-1"
logs_client = boto3.client("logs",   region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
cw_client  = boto3.client("cloudwatch", region_name=REGION)


# ── Invoke a scenario ──────────────────────────────────────────────────────────

def invoke_scenario(function_name: str, scenario: str) -> dict:
    print(f"\n[invoke] {function_name} → scenario={scenario}")
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps({"scenario": scenario}).encode(),
    )
    status    = response["StatusCode"]
    error     = response.get("FunctionError", "none")
    payload   = json.loads(response["Payload"].read())
    print(f"  HTTP status    : {status}")
    print(f"  Function error : {error}")
    print(f"  Payload        : {json.dumps(payload, indent=4)}")
    return payload


# ── Fetch recent CloudWatch log events ────────────────────────────────────────

def fetch_recent_logs(function_name: str, limit: int = 30) -> None:
    log_group = f"/aws/lambda/{function_name}"
    print(f"\n[logs] Fetching last {limit} events from {log_group}")

    try:
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy="LastEventTime",
            descending=True,
            limit=1,
        )["logStreams"]
    except logs_client.exceptions.ResourceNotFoundException:
        print(f"  Log group {log_group} does not exist yet.")
        return

    if not streams:
        print("  No log streams found.")
        return

    stream_name = streams[0]["logStreamName"]
    print(f"  Stream: {stream_name}")

    events = logs_client.get_log_events(
        logGroupName=log_group,
        logStreamName=stream_name,
        limit=limit,
    )["events"]

    for event in events:
        ts = datetime.fromtimestamp(event["timestamp"] / 1000, tz=timezone.utc).strftime("%H:%M:%S")
        print(f"  {ts}  {event['message'].rstrip()}")


# ── CloudWatch Log Insights query ─────────────────────────────────────────────

def run_insights_query(function_name: str, query: str, minutes: int = 60) -> None:
    log_group = f"/aws/lambda/{function_name}"
    end       = datetime.now(tz=timezone.utc)
    start     = end - timedelta(minutes=minutes)

    print(f"\n[insights] Query against {log_group} (last {minutes} min)")
    print(f"  Query: {query}")

    response = logs_client.start_query(
        logGroupName=log_group,
        startTime=int(start.timestamp()),
        endTime=int(end.timestamp()),
        queryString=query,
    )
    query_id = response["queryId"]

    while True:
        result = logs_client.get_query_results(queryId=query_id)
        if result["status"] in ("Complete", "Failed", "Cancelled"):
            break
        print("  ... waiting for query to complete")
        time.sleep(2)

    if result["status"] != "Complete":
        print(f"  Query ended with status: {result['status']}")
        return

    rows = result["results"]
    print(f"  Returned {len(rows)} rows:")
    for row in rows[:20]:
        fields = {f["field"]: f["value"] for f in row}
        print(f"    {json.dumps(fields)}")


# ── CloudWatch Metrics ─────────────────────────────────────────────────────────

def fetch_metrics(function_name: str, minutes: int = 60) -> None:
    end   = datetime.now(tz=timezone.utc)
    start = end - timedelta(minutes=minutes)

    print(f"\n[metrics] CloudWatch Metrics for {function_name} (last {minutes} min)")

    metrics_to_fetch = [
        ("Errors",          "Sum",     "count"),
        ("Duration",        "Average", "ms"),
        ("Throttles",       "Sum",     "count"),
        ("ConcurrentExecutions", "Maximum", "count"),
    ]

    for metric, stat, unit_label in metrics_to_fetch:
        data = cw_client.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName=metric,
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            StartTime=start,
            EndTime=end,
            Period=300,
            Statistics=[stat],
        )["Datapoints"]

        if not data:
            print(f"  {metric:<30} : no data")
        else:
            value = data[-1][stat]
            print(f"  {metric:<30} : {value:.2f} {unit_label}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lambda troubleshooting toolkit")
    parser.add_argument("--function", required=True, help="Lambda function name")
    parser.add_argument("--scenario", help="Invoke a buggy scenario")
    parser.add_argument("--logs",     action="store_true", help="Fetch recent CloudWatch logs")
    parser.add_argument("--insights", help="Run a Log Insights query string")
    parser.add_argument("--metrics",  action="store_true", help="Show CloudWatch metrics")
    parser.add_argument("--minutes",  type=int, default=60, help="Time window in minutes")
    args = parser.parse_args()

    if args.scenario:
        invoke_scenario(args.function, args.scenario)

    if args.logs:
        fetch_recent_logs(args.function)

    if args.insights:
        run_insights_query(args.function, args.insights, args.minutes)

    if args.metrics:
        fetch_metrics(args.function, args.minutes)

    if not any([args.scenario, args.logs, args.insights, args.metrics]):
        parser.print_help()
