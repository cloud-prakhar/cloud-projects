# Step 8 — Cleanup

Tear everything down so nothing bills you. Work top-down: front door → functions → data →
roles → any leftover compute. If you already terminated the EC2 instance in Step 7, skip that
part.

---

## 8.1 Delete the HTTP API

**API Gateway → APIs → `bookstore-api` → Actions → Delete.**

```bash
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='bookstore-api'].ApiId" --output text)
aws apigatewayv2 delete-api --api-id "$API_ID"
```

## 8.2 Delete the Lambda functions

```bash
aws lambda delete-function --function-name bookstore-catalog
aws lambda delete-function --function-name bookstore-orders
```

## 8.3 Delete the DynamoDB tables

> Only after you've confirmed you don't need the data (Step 7 snapshot covers you).

```bash
aws dynamodb delete-table --table-name Books
aws dynamodb delete-table --table-name Orders
```

## 8.4 Delete the IAM roles

Delete inline policies first, then the roles:

```bash
aws iam delete-role-policy --role-name BookstoreCatalogRole --policy-name CatalogBooksRead
aws iam detach-role-policy --role-name BookstoreCatalogRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name BookstoreCatalogRole

aws iam delete-role-policy --role-name BookstoreOrdersRole --policy-name OrdersTablesAccess
aws iam detach-role-policy --role-name BookstoreOrdersRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name BookstoreOrdersRole
```

## 8.5 EC2 + extras

- **Terminate** `bookstore-monolith` if you haven't (Step 7).
- Delete the **security group** you created for it — this only succeeds *after* the instance is
  fully terminated, not merely shutting down, so wait first:

  ```bash
  aws ec2 wait instance-terminated --instance-ids <id>
  aws ec2 delete-security-group --group-id <sg-id>
  ```
- Delete the **EC2 instance role + instance profile** (`BookstoreMonolithRole`, Step 1.2). An
  instance profile has to be emptied before it can be deleted. A role must have its managed
  policies detached **and** its inline policies (Step 2's `BookstoreMigrationWrite`, Step 7's
  `BookstoreSnapshotWrite`) deleted. Otherwise `delete-role` fails with `DeleteConflict: must
  delete policies first`:

  ```bash
  aws iam remove-role-from-instance-profile \
    --instance-profile-name BookstoreMonolithRole --role-name BookstoreMonolithRole
  aws iam delete-instance-profile --instance-profile-name BookstoreMonolithRole
  aws iam detach-role-policy --role-name BookstoreMonolithRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  aws iam delete-role-policy --role-name BookstoreMonolithRole --policy-name BookstoreMigrationWrite
  aws iam delete-role-policy --role-name BookstoreMonolithRole --policy-name BookstoreSnapshotWrite
  aws iam delete-role --role-name BookstoreMonolithRole
  ```
- Delete the CloudWatch log groups `/aws/lambda/bookstore-catalog` and
  `/aws/lambda/bookstore-orders` if you want a clean slate.
- Empty/delete the **S3 snapshot** object/bucket from Step 7 if you no longer need it.
- Deregister the **AMI** and delete its snapshot if you made one.

```bash
aws logs delete-log-group --log-group-name /aws/lambda/bookstore-catalog
aws logs delete-log-group --log-group-name /aws/lambda/bookstore-orders

BKT=bookstore-monolith-snapshot-$(aws sts get-caller-identity --query Account --output text)
aws s3 rm s3://$BKT --recursive
aws s3api delete-bucket --bucket $BKT
```

### Verify nothing is left

Every line below should print empty:

```bash
aws apigatewayv2 get-apis --query "Items[?Name=='bookstore-api'].ApiId" --output text
aws lambda list-functions --query "Functions[?starts_with(FunctionName,'bookstore')].FunctionName" --output text
aws dynamodb list-tables --query "TableNames[?contains(['Books','Orders'],@)]" --output text
aws iam list-roles --query "Roles[?starts_with(RoleName,'Bookstore')].RoleName" --output text
aws iam list-instance-profiles --query "InstanceProfiles[?starts_with(InstanceProfileName,'Bookstore')].InstanceProfileName" --output text
aws ec2 describe-security-groups --filters Name=group-name,Values=bookstore-monolith-sg --query "SecurityGroups[].GroupId" --output text
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/bookstore --query "logGroups[].logGroupName" --output text
```

---

## Checkpoint

- [ ] `bookstore-api` deleted
- [ ] Both Lambda functions deleted
- [ ] `Books` and `Orders` tables deleted
- [ ] Both IAM roles (and their inline policies) deleted
- [ ] EC2 instance terminated; its security group removed
- [ ] EC2 instance role + instance profile deleted (if you made one for SSM)
- [ ] Log groups / S3 snapshot / AMI cleaned up
- [ ] **Billing → Cost Explorer** shows nothing from this project tomorrow

You migrated a monolith to serverless with the Strangler Fig pattern — and left no trace
behind. 🎉
