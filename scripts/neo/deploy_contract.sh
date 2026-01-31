#!/usr/bin/env bash
set -euo pipefail

if ! command -v neoxp >/dev/null 2>&1; then
  echo "neoxp not found. Install Neo Express first:"
  echo "  dotnet tool install -g Neo.Express"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHAIN_FILE="${CHAIN_FILE:-$ROOT_DIR/neo-express.json}"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build}"

mkdir -p "$BUILD_DIR"

python3 - <<'PY'
import sys
try:
    from boa3.boa3 import Boa3
except Exception as exc:
    print("neo3-boa not installed or not available:", exc)
    print("Install with: pip install neo3-boa")
    sys.exit(1)

Boa3.compile_and_save(
    "contracts/permit_registry.py",
    output_path="build"
)
print("Contract compiled into build/permit_registry.nef and build/permit_registry.manifest.json")
PY

NEF_FILE="$BUILD_DIR/permit_registry.nef"
MANIFEST_FILE="$BUILD_DIR/permit_registry.manifest.json"

if [ ! -f "$NEF_FILE" ] || [ ! -f "$MANIFEST_FILE" ]; then
  echo "Compiled NEF or manifest not found. Check neo3-boa output."
  exit 1
fi

ACCOUNT_NAME="${NEO_ACCOUNT:-"validator"}"
ACCOUNT_PASSWORD="${NEO_ACCOUNT_PASSWORD:-"neo"}"

echo "Deploying contract via neoxp..."
DEPLOY_OUT=$(neoxp contract deploy -f "$CHAIN_FILE" -a "$ACCOUNT_NAME" -p "$ACCOUNT_PASSWORD" -i "$NEF_FILE" -m "$MANIFEST_FILE" 2>&1 || true)
echo "$DEPLOY_OUT"

HASH=$(echo "$DEPLOY_OUT" | grep -Eo "0x[a-fA-F0-9]{40}" | tail -n 1)
if [ -z "$HASH" ]; then
  echo "Could not detect contract hash in output."
  exit 1
fi

echo "$HASH" > "$ROOT_DIR/scripts/neo/contract_hash.txt"
echo "Contract deployed: $HASH"
echo "export NEO_CONTRACT_HASH=$HASH"
