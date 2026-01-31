.PHONY: run demo logs

run:
	AUDIT_HMAC_SECRET=demo-secret \
	OLLAMA_BASE_URL=http://127.0.0.1:11434 \
	OLLAMA_MODEL=tinyllama \
	python3 -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000

demo:
	bash scripts/demo_scenario.sh

logs:
	@ls -la data/ || true
	@echo "---- tail audit ----"
	@cat data/audit_log.jsonl | tail -n 1 || true
