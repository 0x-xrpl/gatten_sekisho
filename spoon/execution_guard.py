from datetime import datetime, timezone
from typing import Optional

from spoon.permit import Permit, PermitStore
from spoon.hashing import sha256_hex


class ExecutionGuard:
    def __init__(self, store: PermitStore) -> None:
        self.store = store

    def verify(self, permit_id: str, explain_payload: dict) -> bool:
        permit = self.store.get(permit_id)
        if permit is None:
            return False
        now = datetime.now(timezone.utc)
        if permit.expires_at <= now:
            return False
        decision_hash = sha256_hex(explain_payload)
        return permit.decision_hash == decision_hash
