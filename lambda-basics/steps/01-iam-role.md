# Step 1 — IAM: Create the Lambda Execution Role

Lambda needs an IAM role so the service can:
- Assume the role on your behalf when invoking your function
- Write execution logs to CloudWatch Logs

This role is called the **execution role**. It controls what AWS services your function can call. You will start with the minimum needed: CloudWatch Logs only.

---

## 1.1 Open IAM

1. In the AWS Console, search for **IAM** and open it.
2. In the left sidebar, click **Roles** → **Create role**.

---

## 1.2 Configure the Trust Policy

| Field | Value |
|-------|-------|
| Trusted entity type | **AWS service** |
| Use case | **Lambda** |

Click **Next**.

> **What this does:** The trust policy tells AWS which service is allowed to assume this role. By selecting Lambda, the policy is set so that `lambda.amazonaws.com` can call `sts:AssumeRole`. Without this, Lambda cannot use the role at all.

---

## 1.3 Attach a Permissions Policy

In the search box, type `AWSLambdaBasicExecutionRole` and select the checkbox next to it.

| Policy | Permissions granted |
|--------|---------------------|
| `AWSLambdaBasicExecutionRole` | `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` |

Click **Next**.

> This is the minimum a Lambda function needs to write logs. If your function calls any other AWS service (S3, DynamoDB, etc.) without adding the relevant policy, you'll get `AccessDeniedException` at runtime.

---

## 1.4 Name the Role

| Field | Value |
|-------|-------|
| Role name | `LambdaBasicsExecutionRole` |
| Description | `Basic execution role for HelloWorldLambda — CloudWatch Logs only` |

Click **Create role**.

---

## 1.5 Copy the Role ARN

1. Open the newly created role.
2. Copy the **ARN** shown at the top. It looks like:
   ```
   arn:aws:iam::YOUR_ACCOUNT_ID:role/LambdaBasicsExecutionRole
   ```

You will paste this ARN when creating the Lambda function in Step 2.

---

## AWS CLI (Alternative)

If you prefer the command line:

```bash
# 1. Create the role
aws iam create-role \
  --role-name LambdaBasicsExecutionRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'

# 2. Attach the basic execution policy
aws iam attach-role-policy \
  --role-name LambdaBasicsExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

---

## Checkpoint

- [ ] Role `LambdaBasicsExecutionRole` appears in IAM → Roles
- [ ] Trusted entity shows **lambda.amazonaws.com**
- [ ] Policy `AWSLambdaBasicExecutionRole` is listed under the role
- [ ] You have the Role ARN copied

---

**Next:** [Step 2 — Create and Deploy Your First Lambda Function](./02-create-function.md)
