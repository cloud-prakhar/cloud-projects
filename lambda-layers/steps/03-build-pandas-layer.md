# Step 3 — Build and Publish the Pandas Layer

`pandas` and `numpy` contain **native C extensions** compiled for a specific CPU architecture and operating system. Lambda runs on Amazon Linux 2023 (x86_64). If you install pandas on macOS or Windows, the compiled `.so` files will not work in Lambda.

The safest approach is to build inside a Docker container that matches the Lambda environment.

---

## Option A — With Docker (Recommended)

### Prerequisite

Docker must be installed and running: `docker --version`

If Docker is not available, skip to Option B.

### Build

```bash
cd /path/to/lambda-layers

bash layers/pandas-layer/build.sh
```

The script uses `public.ecr.aws/lambda/python:3.14` — the official AWS Lambda Python 3.14 image — which is identical to the actual Lambda execution environment. Packages compiled inside this container are guaranteed to work in Lambda.

---

## Option B — Without Docker (Linux x86_64 Only)

If you are on Linux x86_64, pip installs platform-compatible wheels:

```bash
PYTHON_VERSION="3.14"
mkdir -p build/pandas-layer/python/lib/python${PYTHON_VERSION}/site-packages

pip install pandas numpy \
  --target "build/pandas-layer/python/lib/python${PYTHON_VERSION}/site-packages" \
  --quiet

cd build/pandas-layer
zip -r ../../pandas-layer.zip python/ --quiet
cd - > /dev/null
echo "pandas-layer.zip created"
```

On macOS or Windows, this will likely fail at Lambda runtime with:
```
ImportError: /var/task/pandas/_libs/lib.so: cannot open shared object file: No such file or directory
```

Use Docker in that case.

---

## Verify the ZIP Structure

```bash
unzip -l pandas-layer.zip | grep -E "__init__.py|\.so" | head -20
```

You should see `.cpython-314-x86_64-linux-gnu.so` files — these are the platform-specific compiled extensions.

---

## Publish the Pandas Layer

```bash
aws lambda publish-layer-version \
  --layer-name PandasLayer \
  --zip-file fileb://pandas-layer.zip \
  --compatible-runtimes python3.14 \
  --description "pandas + numpy for Python 3.14 (Amazon Linux 2023)"
```

Store the ARN:

```bash
PANDAS_LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name PandasLayer \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

echo "Pandas Layer ARN: $PANDAS_LAYER_ARN"
```

---

## Layer Size Check

```bash
ls -lh pandas-layer.zip
```

`pandas` + `numpy` ZIP is typically 15–20 MB, well within Lambda's 50 MB ZIP limit. Unzipped it's ~60 MB (under the 250 MB limit).

---

## Checkpoint

```bash
aws lambda list-layer-versions \
  --layer-name PandasLayer \
  --query 'LayerVersions[*].{Version:Version,ARN:LayerVersionArn}' \
  --output table
```

- [ ] `PandasLayer` version 1 published
- [ ] Layer ARN stored in `$PANDAS_LAYER_ARN`
- [ ] ZIP contains `.so` files (compiled extensions)

---

**Next →** [04-deploy-functions.md](04-deploy-functions.md)
