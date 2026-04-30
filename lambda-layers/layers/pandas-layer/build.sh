#!/usr/bin/env bash
# Build a Lambda Layer containing pandas and numpy.
#
# pandas is a native extension — it must be compiled for the Lambda
# execution environment (Amazon Linux 2023, x86_64). This script builds
# inside the official AWS Lambda Docker image using --entrypoint /bin/bash
# to override the default Lambda entrypoint.
#
# If Docker is unavailable and you are on Linux x86_64 (including WSL2),
# the script falls back to a direct pip install, which produces
# compatible binaries since Lambda also runs on Linux x86_64.
#
# Usage: bash layers/pandas-layer/build.sh

set -euo pipefail

LAYER_NAME="pandas-layer"
PYTHON_VERSION="3.14"
BUILD_DIR="build/${LAYER_NAME}"
OUTPUT_ZIP="${LAYER_NAME}.zip"

echo "==> Cleaning previous build..."
rm -rf "$BUILD_DIR" "$OUTPUT_ZIP"

mkdir -p "${BUILD_DIR}/python/lib/python${PYTHON_VERSION}/site-packages"

if command -v docker &>/dev/null; then
  echo "==> Docker found — building in Lambda-compatible container..."
  # Use --entrypoint /bin/bash to override the Lambda image entrypoint
  docker run --rm \
    --entrypoint /bin/bash \
    -v "$(pwd)/${BUILD_DIR}/python/lib/python${PYTHON_VERSION}/site-packages":/opt/pkg \
    public.ecr.aws/lambda/python:3.14 \
    -c "pip install pandas numpy --target /opt/pkg -q --root-user-action=ignore"
else
  echo "==> Docker not found — installing locally (Linux x86_64 = Lambda-compatible)..."
  pip install pandas numpy \
    --target "${BUILD_DIR}/python/lib/python${PYTHON_VERSION}/site-packages" \
    --quiet
fi

echo "==> Packaging..."
cd "$BUILD_DIR"
zip -r "../../${OUTPUT_ZIP}" python/ --quiet
cd - > /dev/null

echo "==> Layer ZIP: ${OUTPUT_ZIP}"
echo "    Size     : $(du -sh "${OUTPUT_ZIP}" | cut -f1)"
echo ""
echo "Note: Lambda layers have a 250 MB unzipped limit."
echo "      pandas + numpy unzips to ~120 MB — within limits."
echo ""
echo "Next: aws lambda publish-layer-version \\"
echo "        --layer-name PandasLayer \\"
echo "        --zip-file fileb://${OUTPUT_ZIP} \\"
echo "        --compatible-runtimes python3.14 \\"
echo "        --description 'pandas + numpy for Python 3.14 (Amazon Linux 2023)'"
