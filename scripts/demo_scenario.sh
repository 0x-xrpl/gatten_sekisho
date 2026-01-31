#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}
API_KEY=${GATTEN_API_KEY:-}
OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://127.0.0.1:11434}

echo "== GATTEN SEKISHO Demo =="

# Ollama healthcheck
if ! curl -s "${OLLAMA_BASE_URL}/api/tags" >/dev/null; then
  echo "[ERROR] Ollama is not reachable at ${OLLAMA_BASE_URL}"
  echo "Run: ollama serve"
  exit 1
fi

echo "[OK] prerequisites"
echo

echo "---- SCENARIO A: STOP (should be denied/hold) ----"

curl -sS "$BASE_URL/health" | jq .

SUBMIT_PAYLOAD='{
  "user_request": "Deploy the update",
  "context": {
    "tools": ["policy_check", "neo_write", "notify"],
    "environment": "staging"
  }
}'

echo "$SUBMIT_PAYLOAD" | curl -sS -X POST "$BASE_URL/gate/submit" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d @- | tee /tmp/gatten_submit.json | jq .

PERMIT_ID=$(cat /tmp/gatten_submit.json | jq -r '.permit.permit_id')

echo
echo "---- SCENARIO B: GO (permit -> execute) ----"

echo "(Expected: submit returns Permit, execute succeeds with Permit)"

echo
VALID_EXECUTE_PAYLOAD=$(cat <<JSON
{
  "permit_id": "$PERMIT_ID",
  "action": {
    "tool": "neo_write",
    "payload": {}
  }
}
JSON
)

echo "$VALID_EXECUTE_PAYLOAD" | curl -sS -X POST "$BASE_URL/gate/execute" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d @- | jq .

echo
echo "---- SCENARIO C: BLOCK (execute without permit) ----"

echo "(Expected: execute rejects without Permit — Fail-Closed)"

echo
INVALID_EXECUTE_PAYLOAD='{
  "permit_id": "invalid-permit-id",
  "action": {
    "tool": "neo_write",
    "payload": {}
  }
}'

echo "$INVALID_EXECUTE_PAYLOAD" | curl -sS -X POST "$BASE_URL/gate/execute" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d @- | jq .
