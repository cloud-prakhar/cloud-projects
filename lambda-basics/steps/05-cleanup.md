# Step 5 — Cleanup

Remove all resources created in this project to avoid ongoing charges.

---

## Resources to Delete

| Resource | Name |
|----------|------|
| Lambda function | `HelloWorldLambda` |
| IAM role | `LambdaBasicsExecutionRole` |
| CloudWatch log group | `/aws/lambda/HelloWorldLambda` |
| Local ZIP files | `hello_world.zip`, `with_env_vars.zip` |

---

## 5.1 Delete the Lambda Function

1. In the AWS Console, go to **Lambda → Functions**.
2. Select `HelloWorldLambda`.
3. Click **Actions → Delete**.
4. Type `delete` in the confirmation box.
5. Click **Delete**.

> Lambda automatically creates the CloudWatch log group but does **not** delete it when the function is deleted. Do the next step to clean it up.

---

## 5.2 Delete the CloudWatch Log Group

1. In the AWS Console, go to **CloudWatch → Log groups**.
2. Search for `/aws/lambda/HelloWorldLambda`.
3. Select the checkbox next to it.
4. Click **Actions → Delete log group(s)**.
5. Confirm.

---

## 5.3 Delete the IAM Role

1. In the AWS Console, go to **IAM → Roles**.
2. Search for `LambdaBasicsExecutionRole`.
3. Click the role name to open it.
4. Click **Delete**.
5. Type the role name to confirm.

---

## 5.4 Local Cleanup

```bash
rm -f hello_world.zip with_env_vars.zip response.json
```

---

## AWS CLI (Run All at Once)

```bash
# Delete function
aws lambda delete-function --function-name HelloWorldLambda

# Delete log group
aws logs delete-log-group --log-group-name /aws/lambda/HelloWorldLambda

# Detach policy then delete role
aws iam detach-role-policy \
  --role-name LambdaBasicsExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name LambdaBasicsExecutionRole

# Local files
rm -f hello_world.zip with_env_vars.zip response.json
```

---

## Checkpoint

Verify everything is gone:

```bash
aws lambda get-function --function-name HelloWorldLambda 2>&1 | grep -i "not found"
aws iam get-role --role-name LambdaBasicsExecutionRole 2>&1 | grep -i "not found\|cannot be found"
```

---

**Continue to:** [Lambda with S3 Event Processing](../../lambda-s3-event-processing/README.md)
