# Step 2 — Build and Publish the Requests Layer

`requests` is a pure-Python library (no native extensions), so it can be installed on any platform and will work in Lambda without Docker.

---

## Understanding the Layer ZIP Structure

Lambda requires a **specific directory structure** inside the ZIP:

```
requests-layer.zip
└── python/
    └── lib/
        └── python3.14/
            └── site-packages/
                ├── requests/
                ├── urllib3/
                ├── certifi/
                └── charset_normalizer/
```

At runtime, Lambda extracts this to `/opt/` and adds `/opt/python` to `sys.path`. Python then finds packages under `/opt/python/lib/python3.14/site-packages/`.

---

## Step A — Build the Layer

```bash
cd /path/to/lambda-layers

bash layers/requests-layer/build.sh
```

The script:
1. Creates `build/requests-layer/python/lib/python3.14/site-packages/`
2. Installs `requests` and its dependencies there with `pip`
3. ZIPs the `python/` directory tree into `requests-layer.zip`

Verify the ZIP structure:

```bash
unzip -l requests-layer.zip | head -20
```

You should see paths like `python/lib/python3.14/site-packages/requests/__init__.py`.

---

## Step B — Publish the Layer to AWS

```bash
aws lambda publish-layer-version \
  --layer-name RequestsLayer \
  --zip-file fileb://requests-layer.zip \
  --compatible-runtimes python3.14 \
  --description "requests 2.x for Python 3.14"
```

Note the `LayerVersionArn` in the output — you need it to attach the layer to a function:

```json
{
    "LayerArn": "arn:aws:lambda:us-east-1:123456789012:layer:RequestsLayer",
    "LayerVersionArn": "arn:aws:lambda:us-east-1:123456789012:layer:RequestsLayer:1",
    "Version": 1
}
```

Store it:

```bash
REQUESTS_LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name RequestsLayer \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

echo "Requests Layer ARN: $REQUESTS_LAYER_ARN"
```

---

## Layer Versioning

Every time you call `publish-layer-version`, AWS creates a new version (1, 2, 3, …). Old versions remain until you explicitly delete them. Functions always reference a **specific version ARN** — updating the layer does not automatically update functions that use it.

This is intentional: you control when each function adopts a new layer version.

---

## Checkpoint

```bash
aws lambda list-layer-versions \
  --layer-name RequestsLayer \
  --query 'LayerVersions[*].{Version:Version,ARN:LayerVersionArn}' \
  --output table
```

- [ ] `RequestsLayer` version 1 published
- [ ] Layer ARN stored in `$REQUESTS_LAYER_ARN`

---

**Next →** [03-build-pandas-layer.md](03-build-pandas-layer.md)
