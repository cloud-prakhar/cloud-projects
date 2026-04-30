#!/usr/bin/env bash
# Build a Lambda Layer containing the 'requests' package.
#
# Lambda layers must follow this structure:
#   python/lib/python3.14/site-packages/<package>/
#
# The runtime appends /opt/python to sys.path, so packages installed
# under python/lib/python3.14/site-packages/ are importable.
#
# Usage: bash layers/requests-layer/build.sh

set -euo pipefail

LAYER_NAME="requests-layer"
PYTHON_VERSION="3.14"
BUILD_DIR="build/${LAYER_NAME}"
OUTPUT_ZIP="${LAYER_NAME}.zip"

echo "==> Cleaning previous build..."
rm -rf "$BUILD_DIR" "$OUTPUT_ZIP"

echo "==> Installing packages into layer structure..."
mkdir -p "${BUILD_DIR}/python/lib/python${PYTHON_VERSION}/site-packages"

pip install requests \
  --target "${BUILD_DIR}/python/lib/python${PYTHON_VERSION}/site-packages" \
  --quiet

echo "==> Packaging..."
cd "$BUILD_DIR"
zip -r "../../${OUTPUT_ZIP}" python/ --quiet
cd - > /dev/null

echo "==> Layer ZIP: ${OUTPUT_ZIP}"
echo "    Size     : $(du -sh "${OUTPUT_ZIP}" | cut -f1)"
echo ""
echo "Next: aws lambda publish-layer-version \\"
echo "        --layer-name RequestsLayer \\"
echo "        --zip-file fileb://${OUTPUT_ZIP} \\"
echo "        --compatible-runtimes python3.14 \\"
echo "        --description 'requests library for Python 3.14'"
