# Step 4 — Deploy Functions with Layers

Deploy two Lambda functions, each referencing a different layer.

---

## Ensure Layer ARNs Are Set

```bash
REQUESTS_LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name RequestsLayer \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

PANDAS_LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name PandasLayer \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/LambdaLayersExecutionRole"

echo "Requests Layer : $REQUESTS_LAYER_ARN"
echo "Pandas Layer   : $PANDAS_LAYER_ARN"
echo "Role ARN       : $ROLE_ARN"
```

---

## Function 1 — RequestsFunction

```bash
cd /path/to/lambda-layers
zip -j requests_function.zip src/lambda_with_requests.py

aws lambda create-function \
  --function-name RequestsFunction \
  --runtime python3.14 \
  --role "$ROLE_ARN" \
  --handler lambda_with_requests.handler \
  --zip-file fileb://requests_function.zip \
  --layers "$REQUESTS_LAYER_ARN" \
  --timeout 30 \
  --memory-size 128 \
  --description "Project 3: Uses requests via Lambda layer"

aws lambda wait function-active --function-name RequestsFunction
echo "RequestsFunction is Active"
```

---

## Function 2 — PandasFunction

```bash
zip -j pandas_function.zip src/lambda_with_pandas.py

aws lambda create-function \
  --function-name PandasFunction \
  --runtime python3.14 \
  --role "$ROLE_ARN" \
  --handler lambda_with_pandas.handler \
  --zip-file fileb://pandas_function.zip \
  --layers "$PANDAS_LAYER_ARN" \
  --timeout 60 \
  --memory-size 512 \
  --description "Project 3: Uses pandas+numpy via Lambda layer"

aws lambda wait function-active --function-name PandasFunction
echo "PandasFunction is Active"
```

### Why 512 MB for PandasFunction?

pandas loads its entire runtime into memory when imported. 512 MB ensures the cold start doesn't fail with an out-of-memory error. For production, profile your actual memory usage with CloudWatch metrics and tune accordingly.

---

## Verify Layers Are Attached

```bash
# Check RequestsFunction
aws lambda get-function-configuration \
  --function-name RequestsFunction \
  --query 'Layers[*].Arn'

# Check PandasFunction
aws lambda get-function-configuration \
  --function-name PandasFunction \
  --query 'Layers[*].Arn'
```

Each should return the corresponding layer ARN.

---

## What Happens Without the Layer?

Try creating a function without the layer and importing requests:

```bash
# Temporarily update RequestsFunction to have no layers
aws lambda update-function-configuration \
  --function-name RequestsFunction \
  --layers []

aws lambda wait function-updated --function-name RequestsFunction

# Invoke — it will fail with ModuleNotFoundError
aws lambda invoke \
  --function-name RequestsFunction \
  --cli-binary-format raw-in-base64-out \
  --payload '{}' /tmp/no_layer_response.json

cat /tmp/no_layer_response.json
```

You'll see: `"errorMessage": "No module named 'requests'"`

Now restore the layer:

```bash
aws lambda update-function-configuration \
  --function-name RequestsFunction \
  --layers "$REQUESTS_LAYER_ARN"

aws lambda wait function-updated --function-name RequestsFunction
```

This demonstrates precisely what layers provide.

---

## Checkpoint

- [ ] `RequestsFunction` deployed with `RequestsLayer` attached
- [ ] `PandasFunction` deployed with `PandasLayer` attached
- [ ] Deliberately removed layer and confirmed `ModuleNotFoundError`
- [ ] Layer restored

---

**Next →** [05-multiple-layers.md](05-multiple-layers.md)
