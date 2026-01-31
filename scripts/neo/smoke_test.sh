#!/usr/bin/env bash
set -euo pipefail

if ! command -v neoxp >/dev/null 2>&1; then
  echo "neoxp not found. Install Neo Express first:"
  echo "  dotnet tool install -g Neo.Express"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHAIN_FILE="${CHAIN_FILE:-$ROOT_DIR/neo-express.json}"
CONTRACT_HASH="${NEO_CONTRACT_HASH:-$(cat "$ROOT_DIR/scripts/neo/contract_hash.txt" 2>/dev/null || true)}"
RPC_URL="${NEO_RPC_URL:-http://127.0.0.1:50012}"
WIF="${NEO_WIF:-}"

if [ -z "$CONTRACT_HASH" ]; then
  echo "NEO_CONTRACT_HASH not set and scripts/neo/contract_hash.txt not found."
  exit 1
fi

if [ -z "$WIF" ]; then
  echo "NEO_WIF not set. Set it in your env before running this test."
  exit 1
fi

PERMIT_ID="demo-uuid"
DECISION_HASH="0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
ISSUED_AT=$(date +%s)
EXPIRES_AT=$((ISSUED_AT + 3600))
POLICY_VERSION="v1.0"

echo "Invoking register_permit..."
INVOKE_OUT=$(neoxp contract invoke --rpc "$RPC_URL" --wif "$WIF" --hash "$CONTRACT_HASH" \
  --method register_permit \
  --arg "$PERMIT_ID" \
  --arg "$DECISION_HASH" \
  --arg "$ISSUED_AT" \
  --arg "$EXPIRES_AT" \
  --arg "$POLICY_VERSION" 2>&1 || true)
echo "$INVOKE_OUT"

TX_HASH=$(echo "$INVOKE_OUT" | grep -Eo "0x[a-fA-F0-9]{64}" | head -n 1)
echo "tx_hash: ${TX_HASH:-not found}"

echo "Calling get_permit..."
neoxp contract invoke --rpc "$RPC_URL" --hash "$CONTRACT_HASH" \
  --method get_permit \
  --arg "$PERMIT_ID"

echo "Calling is_valid..."
neoxp contract invoke --rpc "$RPC_URL" --hash "$CONTRACT_HASH" \
  --method is_valid \
  --arg "$PERMIT_ID" \
  --arg "$DECISION_HASH" \
  --arg "$ISSUED_AT"
