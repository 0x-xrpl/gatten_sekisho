# GATTEN SEKISHO — Demo (3-minute repro)

This is the shortest reproducible demo path for reviewers.

## Prerequisites
- **Ollama** running locally
- **tinyllama** pulled

```bash
ollama pull tinyllama
ollama serve
```

## 1) Run API
In repo root:

```bash
AUDIT_HMAC_SECRET=demo-secret \
OLLAMA_BASE_URL=http://127.0.0.1:11434 \
OLLAMA_MODEL=tinyllama \
python3 -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

## 2) Run demo scenario
In another terminal:

```bash
make demo
```

Expected:
- `/gate/submit` returns a Permit
- `/gate/execute` succeeds with a valid Permit
- `/gate/execute` rejects without a Permit (Fail-Closed)

## 3) Check audit log (JSONL)

```bash
make logs
```

Optional: Neo real tx
If Neo Express env vars are present, the demo issues a real `neo_tx_hash`.
Otherwise it falls back to MOCK.
