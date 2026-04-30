# Challenges — Lambda Layers

---

## Challenge 1 — Build a Shared Utilities Layer

Create a custom layer that packages your own Python module rather than a third-party library.

1. Create `layers/utils-layer/python/utils/__init__.py` with helper functions (e.g., a `format_response()` helper, a `validate_event()` function)
2. ZIP the `python/` directory and publish as `UtilsLayer`
3. Update `RequestsFunction` to attach both `RequestsLayer` and `UtilsLayer`
4. Import `from utils import format_response` in the handler

This simulates real-world shared utility layers used to avoid code duplication across dozens of Lambda functions.

---

## Challenge 2 — Layer Version Upgrade with Zero-Downtime

Simulate upgrading the `requests` library to a newer version:

1. Build a new layer ZIP with `requests==2.99.0` (or the latest version)
2. Publish it as `RequestsLayer` version 2
3. Update `RequestsFunction` to use version 2
4. Verify the old function still works if you point it back to version 1

This demonstrates that layer version references are pinned — you control rollouts.

---

## Challenge 3 — Layer for a Binary (AWS CLI in Lambda)

Advanced: package the AWS CLI binary as a Lambda layer so your function can shell out to `aws` commands.

1. Download the AWS CLI Linux binary
2. Package it under `/opt/bin/`
3. In the Lambda handler, add `/opt/bin` to `PATH` and call `subprocess.run(["aws", "s3", "ls"])`

This pattern is used when you need a binary tool (ffmpeg, imagemagick, etc.) that is not available in the Lambda runtime.

---

## Challenge 4 — Measure Cold Start Impact by Memory Setting

Write a script that:
1. Invokes `PandasFunction` at 256 MB, 512 MB, and 1024 MB (update and wait between each)
2. Forces a cold start each time (change a description field to trigger a new container)
3. Extracts the `Init Duration` from CloudWatch Logs for each setting
4. Prints a comparison table

You'll see that Lambda allocates CPU proportionally to memory, which directly reduces cold start times.
