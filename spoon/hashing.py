import hashlib
import json
from typing import Any, Dict


def canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(data: Dict[str, Any]) -> str:
    payload = canonical_json(data).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_bytes(data: Dict[str, Any]) -> bytes:
    payload = canonical_json(data).encode("utf-8")
    return hashlib.sha256(payload).digest()
