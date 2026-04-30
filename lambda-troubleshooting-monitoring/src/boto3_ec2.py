"""
Lambda Troubleshooting & Monitoring — Project 4
Boto3 automation: EC2 operations from Lambda.

This handler demonstrates common EC2 automation tasks that Lambda is
frequently used for: listing instances, starting/stopping instances on a
schedule, and tagging resources.

IAM permissions required (in addition to CloudWatch Logs):
  ec2:DescribeInstances
  ec2:StartInstances
  ec2:StopInstances
  ec2:CreateTags

Invoke with:
  {"action": "list"}
  {"action": "stop",  "instance_ids": ["i-0abc123"]}
  {"action": "start", "instance_ids": ["i-0abc123"]}
  {"action": "tag",   "instance_ids": ["i-0abc123"], "tags": {"Env": "dev"}}
"""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ec2 = boto3.client("ec2", region_name=REGION)


def handler(event, context):
    action = event.get("action", "list")
    logger.info("EC2 action: %s | request_id: %s", action, context.aws_request_id)

    if action == "list":
        return _list_instances(event)
    elif action == "stop":
        return _stop_instances(event)
    elif action == "start":
        return _start_instances(event)
    elif action == "tag":
        return _tag_instances(event)
    else:
        return {"statusCode": 400, "body": f"Unknown action: {action}"}


def _list_instances(event: dict) -> dict:
    state_filter = event.get("state", "running")
    paginator = ec2.get_paginator("describe_instances")

    instances = []
    for page in paginator.paginate(
        Filters=[{"Name": "instance-state-name", "Values": [state_filter]}]
    ):
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                name = next(
                    (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
                    "(no name)",
                )
                instances.append({
                    "InstanceId": inst["InstanceId"],
                    "State": inst["State"]["Name"],
                    "Type": inst["InstanceType"],
                    "LaunchTime": inst["LaunchTime"].isoformat(),
                    "Name": name,
                })

    logger.info("Found %d instances in state '%s'", len(instances), state_filter)
    return {"statusCode": 200, "body": json.dumps({"instances": instances})}


def _stop_instances(event: dict) -> dict:
    instance_ids = event.get("instance_ids", [])
    if not instance_ids:
        return {"statusCode": 400, "body": "instance_ids required"}

    response = ec2.stop_instances(InstanceIds=instance_ids)
    transitions = [
        {"id": s["InstanceId"], "previous": s["PreviousState"]["Name"], "current": s["CurrentState"]["Name"]}
        for s in response["StoppingInstances"]
    ]
    logger.info("Stop requested: %s", json.dumps(transitions))
    return {"statusCode": 200, "body": json.dumps({"transitions": transitions})}


def _start_instances(event: dict) -> dict:
    instance_ids = event.get("instance_ids", [])
    if not instance_ids:
        return {"statusCode": 400, "body": "instance_ids required"}

    response = ec2.start_instances(InstanceIds=instance_ids)
    transitions = [
        {"id": s["InstanceId"], "previous": s["PreviousState"]["Name"], "current": s["CurrentState"]["Name"]}
        for s in response["StartingInstances"]
    ]
    logger.info("Start requested: %s", json.dumps(transitions))
    return {"statusCode": 200, "body": json.dumps({"transitions": transitions})}


def _tag_instances(event: dict) -> dict:
    instance_ids = event.get("instance_ids", [])
    tags_dict = event.get("tags", {})
    if not instance_ids or not tags_dict:
        return {"statusCode": 400, "body": "instance_ids and tags required"}

    tags = [{"Key": k, "Value": v} for k, v in tags_dict.items()]
    ec2.create_tags(Resources=instance_ids, Tags=tags)
    logger.info("Tagged %d instances: %s", len(instance_ids), json.dumps(tags_dict))
    return {"statusCode": 200, "body": json.dumps({"tagged": instance_ids, "tags": tags_dict})}
