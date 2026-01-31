import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

from spoon.config import SETTINGS
from spoon.tools.storage_tool import StorageTool


class AuditLogger:
    def __init__(self, storage: StorageTool) -> None:
        self.storage = storage
        self._path = os.path.join(self.storage.base_dir, "audit_log.jsonl")
        self._last_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        if not os.path.exists(self._path):
            return ""
        last = ""
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    last = data.get("hash", last)
                except json.JSONDecodeError:
                    continue
        return last

    def _hash_entry(self, payload: Dict[str, Any], prev_hash: str) -> str:
        digest = hashlib.sha256()
        digest.update(prev_hash.encode("utf-8"))
        digest.update(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        return digest.hexdigest()

    def _sign(self, entry_hash: str) -> Optional[str]:
        if SETTINGS.audit_hmac_secret:
            return hmac.new(
                SETTINGS.audit_hmac_secret.encode("utf-8"),
                entry_hash.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        if SETTINGS.strict_mode and not SETTINGS.audit_allow_unsigned:
            raise RuntimeError("AUDIT_HMAC_SECRET is required in strict mode")
        return None

    def append(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        record["timestamp"] = int(time.time())
        record["prev_hash"] = self._last_hash
        record["hash"] = self._hash_entry(record, self._last_hash)
        record["hmac"] = self._sign(record["hash"])

        self.storage.append_jsonl("audit_log.jsonl", record)
        self._last_hash = record["hash"]
        return record

    def find_latest_by_permit_id(self, permit_id: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self._path):
            return None
        latest = None
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                permit = data.get("permit") or {}
                if permit.get("permit_id") == permit_id:
                    latest = data
        return latest
