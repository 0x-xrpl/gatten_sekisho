import json
from typing import Any, Dict, List

from spoon_ai.tools.base import BaseTool

from spoon.config import SETTINGS


def _load_policy(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class PolicyTool(BaseTool):
    name: str = "policy_check"
    description: str = "Validate decision against policies"
    parameters: dict = {
        "type": "object",
        "properties": {
            "decision": {"type": "string"},
            "context": {"type": "object"},
        },
        "required": ["decision"],
    }
    policy_path: str = SETTINGS.policy_path

    def _load(self) -> Dict[str, Any]:
        return _load_policy(self.policy_path)

    @property
    def version(self) -> str:
        return self._load().get("version", "v1.0")

    async def execute(self, decision: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}
        policy = self._load()
        lowered = decision.lower()
        violations: List[str] = []
        required_human_approval = False
        risk_level = "LOW"

        for rule in policy.get("rules", []):
            patterns = [p.lower() for p in rule.get("patterns", [])]
            if any(p in lowered for p in patterns):
                if rule.get("type") == "blocklist":
                    violations.append(rule.get("message", rule.get("id", "policy_violation")))
                    risk_level = "HIGH"
                elif rule.get("type") == "require_approval":
                    required_human_approval = True
                    risk_level = "MEDIUM"

        registered_tools = set(policy.get("registered_tools", []))
        requested_tools = set(context.get("tools", [])) if isinstance(context.get("tools"), list) else set()
        unknown_tools = requested_tools - registered_tools
        if unknown_tools:
            violations.append(f"unregistered tools: {', '.join(sorted(unknown_tools))}")
            risk_level = "HIGH"

        return {
            "ok": len(violations) == 0 and not required_human_approval,
            "violations": violations,
            "risk_level": risk_level,
            "required_human_approval": required_human_approval,
        }
