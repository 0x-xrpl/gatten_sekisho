import os
import tempfile
import unittest

from spoon.audit import AuditLogger
from spoon.orchestrator import Orchestrator
from spoon.permit import PermitIssuer
from spoon.status import APPROVED, EXECUTED, REJECTED
from spoon.tools.storage_tool import StorageTool

import spoon.config as config


class TestExecuteFlow(unittest.TestCase):
    def setUp(self) -> None:
        object.__setattr__(config.SETTINGS, "audit_hmac_secret", "test-secret")

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

    def test_execute_rejects_without_permit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            orch = Orchestrator(policy_path=os.path.join(base_dir, "policies", "policy.json"), data_dir=tmp)
            result = orch.execute("missing-permit", action={"tool": "storage", "payload": {}})
            self.assertEqual(result["status"], REJECTED)

    def test_execute_accepts_with_valid_permit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            orch = Orchestrator(policy_path=os.path.join(base_dir, "policies", "policy.json"), data_dir=tmp)
            storage = StorageTool(tmp)
            issuer = PermitIssuer(storage, ttl_seconds=300)
            explain = self._explain_payload()
            permit = issuer.issue(
                explain_payload=explain,
                policy_version="v1.0",
                risk_level="LOW",
                neo_tx_hash="MOCK_TX",
                permit_id="permit-1",
                neo_mode="mock",
            )
            orch.permit_store.save(permit)
            audit = AuditLogger(storage)
            audit.append(
                {
                    "permit": permit.to_dict(),
                    "explain": explain,
                    "policy": {"ok": True},
                    "status": APPROVED,
                    "final_status": APPROVED,
                }
            )
            result = orch.execute(
                "permit-1",
                action={"tool": "storage", "payload": {"filename": "exec.jsonl", "payload": {"ok": True}}},
            )
            self.assertEqual(result["status"], EXECUTED)


if __name__ == "__main__":
    unittest.main()
