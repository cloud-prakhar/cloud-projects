# Step 6 — Cleanup

Remove all resources created in this project.

---

## Resources to Delete

| Resource | Name |
|----------|------|
| Lambda function | `S3FileProcessor` |
| S3 source bucket | `lambda-s3-source-<account-id>` |
| S3 destination bucket | `lambda-s3-dest-<account-id>` |
| IAM inline policy | `S3ReadWritePolicy` (on `LambdaS3ProcessorRole`) |
| IAM managed policy | `AWSLambdaBasicExecutionRole` (on `LambdaS3ProcessorRole`) |
| IAM role | `LambdaS3ProcessorRole` |
| CloudWatch log group | `/aws/lambda/S3FileProcessor` |

---

## Cleanup Script

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SOURCE_BUCKET="lambda-s3-source-${ACCOUNT_ID}"
DEST_BUCKET="lambda-s3-dest-${ACCOUNT_ID}"

# 1. Remove the S3 event notification (before deleting Lambda,
#    to stop new invocations from being triggered during cleanup)
aws s3api put-bucket-notification-configuration \
  --bucket "$SOURCE_BUCKET" \
  --notification-configuration '{}'
echo "✓ S3 event notification removed"

# 2. Delete Lambda function
aws lambda delete-function --function-name S3FileProcessor
echo "✓ Lambda function deleted"

# 3. Empty and delete S3 buckets
# S3 requires buckets to be empty before deletion.
# If versioning was enabled, also delete version markers.
aws s3 rm "s3://${SOURCE_BUCKET}" --recursive
aws s3api delete-bucket --bucket "$SOURCE_BUCKET"
echo "✓ Source bucket deleted"

aws s3 rm "s3://${DEST_BUCKET}" --recursive
aws s3api delete-bucket --bucket "$DEST_BUCKET"
echo "✓ Destination bucket deleted"

# 4. Delete CloudWatch log group
aws logs delete-log-group \
  --log-group-name /aws/lambda/S3FileProcessor
echo "✓ Log group deleted"

# 5. Detach policies and delete IAM role
aws iam detach-role-policy \
  --role-name LambdaS3ProcessorRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role-policy \
  --role-name LambdaS3ProcessorRole \
  --policy-name S3ReadWritePolicy

aws iam delete-role --role-name LambdaS3ProcessorRole
echo "✓ IAM role deleted"

# 6. Local cleanup
rm -f s3_processor.zip /tmp/test_event.json /tmp/response.json
echo "✓ Local files cleaned"

echo ""
echo "All resources deleted."
```

---

## If Versioning Was Enabled on the Source Bucket

If you enabled versioning in Step 2, `aws s3 rm --recursive` only deletes the current versions, leaving delete markers. Clean those up first:

```bash
# Delete all versions and delete markers
aws s3api list-object-versions \
  --bucket "$SOURCE_BUCKET" \
  --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
  --output json | \
  python3 -c "
import json, sys, subprocess
data = json.load(sys.stdin)
for obj in data.get('Objects', []):
    subprocess.run(['aws','s3api','delete-object',
        '--bucket','$SOURCE_BUCKET',
        '--key', obj['Key'],
        '--version-id', obj['VersionId']])
print('Versions cleared')
"

# Then delete the bucket
aws s3api delete-bucket --bucket "$SOURCE_BUCKET"
```

---

## Verification

```bash
# Lambda: should error with "Function not found"
aws lambda get-function --function-name S3FileProcessor 2>&1 | grep -i "not found"

# S3: buckets should not appear
aws s3api list-buckets \
  --query "Buckets[?contains(Name, 'lambda-s3')].Name"

# IAM: role should not exist
aws iam get-role --role-name LambdaS3ProcessorRole 2>&1 | grep -i "not found\|cannot be found"
```

---

**Continue →** [Lambda Layers](../../lambda-layers/README.md)
