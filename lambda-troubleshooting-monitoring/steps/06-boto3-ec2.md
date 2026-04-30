# Step 6 — EC2 Automation with Lambda and Boto3

Deploy the EC2 automation function. This is a common pattern for:
- **Scheduled start/stop** of dev instances to reduce cost (via EventBridge)
- **Auto-tagging** untagged instances for compliance
- **Inventory reporting** — list instances missing required tags

> No new EC2 instances are created in this project. The function queries and manages **existing** instances, so there is no EC2 running cost.

---

## 6.1 Package and Create the Function

```bash
cd /path/to/lambda-troubleshooting-monitoring
zip -j ec2_automation.zip src/boto3_ec2.py
```

1. Open **Lambda** → **Create function** → **Author from scratch**.

   | Field | Value |
   |-------|-------|
   | Function name | `EC2AutomationFn` |
   | Runtime | **Python 3.14** |

2. **Permissions**: Use existing role `LambdaTroubleshootingRole`.
3. Click **Create function**.
4. Upload `ec2_automation.zip` → set Handler to `boto3_ec2.handler` → Timeout 30 sec.
5. Click **Save**.

---

## 6.2 Test: List EC2 Instances

Create a test event:

1. **Test** tab → **Create new event** → Event name: `ListRunning`
2. Paste:
   ```json
   { "action": "list", "state": "running" }
   ```
3. Click **Test**.

Expected response — if you have no running instances:

```json
{ "statusCode": 200, "body": "{\"instances\": []}" }
```

An empty list is correct, not an error. Try listing stopped instances too:

```json
{ "action": "list", "state": "stopped" }
```

---

## 6.3 Test: Tag an Instance (Requires an Existing Instance)

If you have an EC2 instance in your account:

1. Event name: `TagInstance`
2. Paste (replace the instance ID):
   ```json
   {
     "action": "tag",
     "instance_ids": ["i-0your_instance_id"],
     "tags": {"ManagedBy": "Lambda", "Project": "troubleshooting"}
   }
   ```
3. Click **Test**.
4. Verify the tags in **EC2 → Instances → select instance → Tags** tab.

---

## 6.4 Understand the Boto3 Pagination Pattern

Open `src/boto3_ec2.py` and look at `_list_instances()`:

```python
paginator = ec2.get_paginator("describe_instances")
for page in paginator.paginate(...):
    ...
```

Without pagination, `describe_instances` returns at most 1000 results. In large accounts, a non-paginated call silently truncates. Always use paginators for `Describe*` calls in production.

---

## Checkpoint

- [ ] `EC2AutomationFn` deployed and Active
- [ ] List action returned a valid response (empty list is fine)
- [ ] Can explain why paginators matter for `Describe*` calls

---

**Next:** [Step 7 — S3 Automation](./07-boto3-s3.md)
