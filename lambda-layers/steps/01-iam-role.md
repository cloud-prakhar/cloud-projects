# Step 1 — Create the IAM Execution Role

The functions in this project make outbound HTTP calls (`requests.get()`). Lambda functions that make outbound internet calls do not need any special IAM permissions for the call itself — they just need to be in a VPC with a NAT gateway, or (more simply for learning) they run in the default non-VPC configuration which has outbound internet access by default.

You only need IAM permissions for the CloudWatch Logs write.

---

## Create the Role

```bash
aws iam create-role \
  --role-name LambdaLayersExecutionRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name LambdaLayersExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

---

## Verify

```bash
aws iam get-role \
  --role-name LambdaLayersExecutionRole \
  --query 'Role.{ARN:Arn, Created:CreateDate}' \
  --output table
```

---

## Checkpoint

- [ ] Role `LambdaLayersExecutionRole` exists
- [ ] Trust policy allows `lambda.amazonaws.com`
- [ ] `AWSLambdaBasicExecutionRole` attached

---

**Next →** [02-build-requests-layer.md](02-build-requests-layer.md)
