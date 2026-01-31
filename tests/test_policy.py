import asyncio
import os
import unittest

from spoon.tools.policy_tool import PolicyTool


class TestPolicyTool(unittest.TestCase):
    def setUp(self) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.policy = PolicyTool(policy_path=os.path.join(base_dir, "policies", "policy.json"))

    def test_blocklist_violation(self) -> None:
        result = asyncio.run(
            self.policy.execute("delete all records", {"tools": ["policy"]})
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["violations"])

    def test_require_approval(self) -> None:
        result = asyncio.run(
            self.policy.execute("transfer funds", {"tools": ["policy"]})
        )
        self.assertTrue(result["required_human_approval"])


if __name__ == "__main__":
    unittest.main()
