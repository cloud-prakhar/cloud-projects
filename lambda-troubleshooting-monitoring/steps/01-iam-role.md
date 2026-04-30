# Step 1 — Create the IAM Execution Role

This project's functions touch EC2, S3, SQS, and CloudWatch Logs. You'll create one shared execution role with a scoped inline policy for each service.

---

## Create the Base Role

```bash
aws iam create-role \
  --role-name LambdaTroubleshootingRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name LambdaTroubleshootingRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

---

## Attach EC2 Read/Write Policy

Scoped to describe, start/stop, and tag — no `ec2:*`:

```bash
aws iam put-role-policy \
  --role-name LambdaTroubleshootingRole \
  --policy-name EC2AutomationPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ec2:DescribeInstances",
          "ec2:StartInstances",
          "ec2:StopInstances",
          "ec2:CreateTags"
        ],
        "Resource": "*"
      }
    ]
  }'
```

> `ec2:DescribeInstances` and `ec2:CreateTags` do not support resource-level restrictions in IAM — `Resource: "*"` is required for those.

---

## Attach S3 Policy

```bash
aws iam put-role-policy \
  --role-name LambdaTroubleshootingRole \
  --policy-name S3AutomationPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:ListAllMyBuckets",
          "s3:ListBucket",
          "s3:GetObject",
          "s3:CopyObject",
          "s3:PutObject"
        ],
        "Resource": "*"
      }
    ]
  }'
```

---

## Attach SQS Policy

```bash
aws iam put-role-policy \
  --role-name LambdaTroubleshootingRole \
  --policy-name SQSAutomationPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
          "sqs:PurgeQueue"
        ],
        "Resource": "*"
      }
    ]
  }'
```

---

## Verify

```bash
aws iam list-role-policies \
  --role-name LambdaTroubleshootingRole \
  --query 'PolicyNames'
```

Expected: `["EC2AutomationPolicy", "S3AutomationPolicy", "SQSAutomationPolicy"]`

```bash
aws iam list-attached-role-policies \
  --role-name LambdaTroubleshootingRole \
  --query 'AttachedPolicies[*].PolicyName'
```

Expected: `["AWSLambdaBasicExecutionRole"]`

---

## Checkpoint

- [ ] Role `LambdaTroubleshootingRole` created
- [ ] All three inline policies attached
- [ ] `AWSLambdaBasicExecutionRole` managed policy attached

---

**Next →** [02-setup-buggy-function.md](02-setup-buggy-function.md)
