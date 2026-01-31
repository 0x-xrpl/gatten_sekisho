import os
import tempfile
import unittest

from spoon.orchestrator import Orchestrator
from spoon.status import DENIED

import spoon.config as config


class TestFailClosed(unittest.TestCase):
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

    def test_policy_tool_fail_closed_on_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            orch = Orchestrator(policy_path=os.path.join(base_dir, "policies", "policy.json"), data_dir=tmp)

            orch.decision_agent.run = lambda user_request, context, request_id="": {
                "draft_decision": "Deploy",
                "context": context,
            }
            orch.explain_agent.run = lambda user_request, draft_decision, context: self._explain_payload()

            async def boom(*args, **kwargs):
                raise RuntimeError("boom")

            orch.policy_tool.execute = boom

            result = orch.run("test", {})
            self.assertEqual(result["status"], DENIED)


if __name__ == "__main__":
    unittest.main()
