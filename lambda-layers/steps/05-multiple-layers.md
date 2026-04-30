# Step 5 — Attach Multiple Layers to One Function

A single Lambda function can use up to **5 layers** simultaneously. This is useful when you have a shared utilities layer, a shared data-science library layer, and function-specific dependencies all at once.

In this step you update `PandasFunction` to also include `RequestsLayer` so it can make HTTP calls **and** use pandas.

---

## Attach Both Layers

```bash
REQUESTS_LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name RequestsLayer \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

PANDAS_LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name PandasLayer \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

aws lambda update-function-configuration \
  --function-name PandasFunction \
  --layers "$PANDAS_LAYER_ARN" "$REQUESTS_LAYER_ARN"

aws lambda wait function-updated --function-name PandasFunction
echo "PandasFunction now has both layers"
```

> Pass all layers in a single `--layers` call. Each call **replaces** the existing layer list — it does not append.

---

## Verify

```bash
aws lambda get-function-configuration \
  --function-name PandasFunction \
  --query 'Layers[*].{ARN:Arn}' \
  --output table
```

Both layer ARNs should appear.

---

## Layer Ordering and Conflicts

When two layers contain files at the same path, the **later layer** in the list wins (layers are applied in order). This means:

- If `PandasLayer` contains `numpy/__init__.py` and `RequestsLayer` also somehow ships a different `numpy` (unlikely but possible), the one in `RequestsLayer` (listed second) takes precedence.
- Order layers defensively: most-specific last.

For standard library layers this is rarely an issue. Be cautious when building custom shared utility layers.

---

## Inspect Layer Contents at Runtime

You can have Lambda print what's actually on the path from inside the function. Add this to any handler temporarily:

```python
import os, sys
print("sys.path:", sys.path)
print("/opt/python contents:", os.listdir("/opt/python") if os.path.exists("/opt/python") else "not found")
```

This is useful to debug import errors when layers don't seem to be loading correctly.

---

## Checkpoint

- [ ] `PandasFunction` has both `PandasLayer` and `RequestsLayer` attached
- [ ] Confirmed via `get-function-configuration`
- [ ] Understand that `--layers` replaces, not appends

---

**Next →** [06-testing.md](06-testing.md)
