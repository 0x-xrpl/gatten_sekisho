#!/usr/bin/env bash
set -euo pipefail

if ! command -v neoxp >/dev/null 2>&1; then
  echo "neoxp not found. Install Neo Express first:"
  echo "  dotnet tool install -g Neo.Express"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHAIN_FILE="${CHAIN_FILE:-$ROOT_DIR/neo-express.json}"
RPC_HOST="${RPC_HOST:-127.0.0.1}"
RPC_PORT="${RPC_PORT:-50012}"

if [ ! -f "$CHAIN_FILE" ]; then
  echo "Creating Neo Express chain at $CHAIN_FILE"
  neoxp create -f "$CHAIN_FILE" --force --count 1
fi

echo "Starting Neo Express RPC at http://$RPC_HOST:$RPC_PORT"
neoxp run -f "$CHAIN_FILE" --rpc "$RPC_HOST:$RPC_PORT"

echo ""
echo "If you need a signing key (WIF), run:"
echo "  neoxp show addresses -f \"$CHAIN_FILE\""
echo "Copy a WIF and set it in .env as NEO_WIF."
echo ""
echo "Reset chain (destructive):"
echo "  neoxp reset -f \"$CHAIN_FILE\" --force"
