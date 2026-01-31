import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from spoon.hashing import sha256_hex
from spoon.tools.storage_tool import StorageTool


@dataclass
class Permit:
    permit_id: str
    decision_hash: str
    policy_version: str
    risk_level: str
    issued_at: datetime
    expires_at: datetime
    neo_tx_hash: str
    neo_mode: str = "mock"

    def to_dict(self) -> Dict[str, str]:
        payload = asdict(self)
        payload["issued_at"] = self.issued_at.isoformat()
        payload["expires_at"] = self.expires_at.isoformat()
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, str]) -> "Permit":
        return cls(
            permit_id=payload["permit_id"],
            decision_hash=payload["decision_hash"],
            policy_version=payload["policy_version"],
            risk_level=payload["risk_level"],
            issued_at=datetime.fromisoformat(payload["issued_at"]),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            neo_tx_hash=payload["neo_tx_hash"],
            neo_mode=payload.get("neo_mode", "mock"),
        )


class PermitStore:
    def __init__(self, storage: StorageTool) -> None:
        self.storage = storage
        self._cache: Dict[str, Permit] = {}
        self._path = os.path.join(self.storage.base_dir, "permits.jsonl")
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    permit = Permit.from_dict(json.loads(line))
                    self._cache[permit.permit_id] = permit

    def save(self, permit: Permit) -> None:
        self._cache[permit.permit_id] = permit
        self.storage.append_jsonl("permits.jsonl", permit.to_dict())

    def get(self, permit_id: str) -> Optional[Permit]:
        return self._cache.get(permit_id)


class PermitIssuer:
    def __init__(self, storage: StorageTool, ttl_seconds: int = 300) -> None:
        self.storage = storage
        self.ttl_seconds = ttl_seconds

    def issue(
        self,
        explain_payload: Dict[str, str],
        policy_version: str,
        risk_level: str,
        neo_tx_hash: str,
        permit_id: str,
        neo_mode: str = "mock",
    ) -> Permit:
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + timedelta(seconds=self.ttl_seconds)
        decision_hash = sha256_hex(explain_payload)
        permit = Permit(
            permit_id=permit_id,
            decision_hash=decision_hash,
            policy_version=policy_version,
            risk_level=risk_level,
            issued_at=issued_at,
            expires_at=expires_at,
            neo_tx_hash=neo_tx_hash,
            neo_mode=neo_mode,
        )
        return permit
