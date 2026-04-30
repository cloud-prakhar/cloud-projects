# Troubleshooting — Lambda Layers

---

## Error: `ModuleNotFoundError: No module named 'requests'`

**Cause:** The layer is not attached, was detached, or the layer ZIP structure is wrong.

**Diagnosis:**

```bash
# Check if the layer is attached
aws lambda get-function-configuration \
  --function-name RequestsFunction \
  --query 'Layers[*].Arn'

# If no layers returned, re-attach:
aws lambda update-function-configuration \
  --function-name RequestsFunction \
  --layers "$REQUESTS_LAYER_ARN"
```

**Verify ZIP structure:**

```bash
unzip -l requests-layer.zip | head -10
```

The first path must start with `python/lib/python3.14/site-packages/`, not `site-packages/` or `requests/` directly.

---

## Error: `ImportError: ... cannot open shared object file`

**Cause:** The pandas or numpy `.so` files were compiled for a different OS/architecture (e.g., macOS arm64) but Lambda runs on Linux x86_64.

**Fix:** Rebuild the pandas layer using Docker:

```bash
bash layers/pandas-layer/build.sh
```

The Docker build uses the official Lambda base image for Linux x86_64 and produces compatible binaries.

---

## Error: Layer size exceeds limit

**Symptom:** `aws lambda publish-layer-version` fails with:
```
CodeStorageExceededException: You have exceeded your maximum total code size per account.
```

Or:
```
InvalidParameterValueException: Unzipped size must be smaller than...
```

**Fix:** Reduce the layer size:

```bash
# Remove test files and __pycache__
find build/pandas-layer -name "*.pyc" -delete
find build/pandas-layer -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find build/pandas-layer -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null
find build/pandas-layer -name "tests" -type d -exec rm -rf {} + 2>/dev/null

# Repack
cd build/pandas-layer
zip -r ../../pandas-layer-slim.zip python/ --quiet
cd - > /dev/null
```

---

## Layer works locally but fails in Lambda

**Symptom:** You can `import pandas` locally, but Lambda returns an ImportError.

**Cause:** The local install is for your OS, but Lambda runs Amazon Linux 2023. Python packages with C extensions must match the target OS and CPU architecture.

**Fix:** Always build native extension layers (pandas, numpy, Pillow, etc.) inside the Lambda Docker container:

```bash
docker run --rm \
  -v "$(pwd)/build/pandas-layer/python/lib/python3.14/site-packages":/opt/pkg \
  public.ecr.aws/lambda/python:3.14 \
  pip install pandas numpy --target /opt/pkg --quiet
```

---

## Function has the layer but old version is being used

**Cause:** You published a new layer version (e.g., version 2) but the function still references version 1.

**Fix:** Update the function to use the new ARN:

```bash
# Get the latest version ARN
NEW_ARN=$(aws lambda list-layer-versions \
  --layer-name RequestsLayer \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

aws lambda update-function-configuration \
  --function-name RequestsFunction \
  --layers "$NEW_ARN"
```

---

## `--layers []` doesn't remove layers via CLI

**Cause:** The AWS CLI does not accept an empty JSON array literal directly for `--layers`.

**Fix:**

```bash
# Remove all layers from a function
aws lambda update-function-configuration \
  --function-name RequestsFunction \
  --layers
# Note: just pass --layers with no value — or omit it entirely and use a JSON file

# Alternative: use --cli-input-json
aws lambda update-function-configuration \
  --cli-input-json '{"FunctionName":"RequestsFunction","Layers":[]}'
```

---

## Cold start is very slow (>3 seconds)

**Cause:** pandas/numpy import time dominates cold starts at 512 MB memory. Higher memory also increases CPU allocation.

**Fix:** Increase memory to reduce import time (Lambda gives more CPU with more memory):

```bash
aws lambda update-function-configuration \
  --function-name PandasFunction \
  --memory-size 1024
```

At 1024 MB, the pandas cold start typically drops from ~1800 ms to ~900 ms.
