# Step 7 — Cleanup

---

## Resources to Delete

| Resource | Name |
|----------|------|
| Lambda function | `RequestsFunction` |
| Lambda function | `PandasFunction` |
| Lambda layer version | `RequestsLayer:1` |
| Lambda layer version | `PandasLayer:1` |
| IAM role | `LambdaLayersExecutionRole` |
| CloudWatch log groups | `/aws/lambda/RequestsFunction`, `/aws/lambda/PandasFunction` |
| Local files | `requests-layer.zip`, `pandas-layer.zip`, `*.zip`, `build/` |

---

## Cleanup Script

```bash
# 1. Delete Lambda functions
aws lambda delete-function --function-name RequestsFunction
aws lambda delete-function --function-name PandasFunction
echo "✓ Functions deleted"

# 2. Delete layer versions
REQUESTS_VERSION=$(aws lambda list-layer-versions \
  --layer-name RequestsLayer \
  --query 'LayerVersions[0].Version' --output text)

PANDAS_VERSION=$(aws lambda list-layer-versions \
  --layer-name PandasLayer \
  --query 'LayerVersions[0].Version' --output text)

aws lambda delete-layer-version \
  --layer-name RequestsLayer \
  --version-number "$REQUESTS_VERSION"

aws lambda delete-layer-version \
  --layer-name PandasLayer \
  --version-number "$PANDAS_VERSION"
echo "✓ Layer versions deleted"

# 3. Delete CloudWatch log groups
aws logs delete-log-group --log-group-name /aws/lambda/RequestsFunction 2>/dev/null
aws logs delete-log-group --log-group-name /aws/lambda/PandasFunction 2>/dev/null
echo "✓ Log groups deleted"

# 4. Delete IAM role
aws iam detach-role-policy \
  --role-name LambdaLayersExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name LambdaLayersExecutionRole
echo "✓ IAM role deleted"

# 5. Local cleanup
rm -rf build/ *.zip /tmp/requests_response.json /tmp/pandas_response.json /tmp/warm_response.json
echo "✓ Local files cleaned"
```

---

## Note on Layer Deletion

Deleting a layer version does not affect functions already using it. Functions hold a reference to the specific layer version ARN. The layer content remains accessible to those functions even after deletion — it's just hidden from the version list and cannot be used by new functions.

To truly remove a layer from a function, update the function's layer list to exclude it.

---

**Continue →** [Lambda Troubleshooting & Monitoring](../../lambda-troubleshooting-monitoring/README.md)
