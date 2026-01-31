# GATTEN SEKISHO UI — Demo Guide

## Prerequisites
- Ollama running
- Backend running
- UI running

## Start backend
```bash
cd /Users/mee/Documents/gatten_sekisho
AUDIT_HMAC_SECRET=demo-secret OLLAMA_BASE_URL=http://127.0.0.1:11434 OLLAMA_MODEL=tinyllama \
python3 -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

## Start UI
```bash
cd /Users/mee/Documents/gatten_sekisho/ui
npm install
npm run dev
```

## Environment
If backend is not on 8000, set:
```bash
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

## Demo steps (UI only)
1) **Execute WITHOUT Permit** → REJECTED (Fail-Closed)
2) **SAFE** → Submit → Permit ISSUED → Execute success (GO)
3) **DANGEROUS** → Submit → DENIED (STOP)

## Common issues
- **8000 already used**: stop other servers or change API port
- **Wrong Server**: /openapi.json is reachable but missing /gate endpoints
- **422 errors**: UI payload mismatch; refresh to re-pull OpenAPI
