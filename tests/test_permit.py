import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from spoon.execution_guard import ExecutionGuard
from spoon.permit import PermitIssuer, PermitStore
from spoon.tools.storage_tool import StorageTool


class TestPermitFlow(unittest.TestCase):
    def _explain_payload(self):
        return {
            "decision": "Deploy",
            "rationale": ["ok"],
            "assumptions": ["ok"],
            "risks": [
                {"risk": "Risk", "severity": "LOW", "mitigation": "Mitigate"}
            ],
            "alternatives": [{"option": "Alt", "why_not": "Slower"}],
        }

    def test_exec_denied_without_permit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = PermitStore(StorageTool(tmp))
            guard = ExecutionGuard(store)
            allowed = guard.verify("missing", self._explain_payload())
            self.assertFalse(allowed)

    def test_exec_allowed_with_valid_permit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage = StorageTool(tmp)
            store = PermitStore(storage)
            issuer = PermitIssuer(storage, ttl_seconds=60)
            permit = issuer.issue(
                explain_payload=self._explain_payload(),
                policy_version="v1.0",
                risk_level="LOW",
                neo_tx_hash="0x123",
                permit_id="permit-1",
            )
            store.save(permit)
            guard = ExecutionGuard(store)
            self.assertTrue(guard.verify("permit-1", self._explain_payload()))

    def test_exec_denied_expired_permit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage = StorageTool(tmp)
            store = PermitStore(storage)
            issuer = PermitIssuer(storage, ttl_seconds=1)
            permit = issuer.issue(
                explain_payload=self._explain_payload(),
                policy_version="v1.0",
                risk_level="LOW",
                neo_tx_hash="0x123",
                permit_id="permit-2",
            )
            permit.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            store.save(permit)
            guard = ExecutionGuard(store)
            self.assertFalse(guard.verify("permit-2", self._explain_payload()))


if __name__ == "__main__":
    unittest.main()
