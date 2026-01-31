from typing import Any, Dict

from spoon.llm import SpoonLLM


class ExplainAgent:
    def __init__(self, llm: SpoonLLM) -> None:
        self.llm = llm

    def run(self, user_request: str, draft_decision: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Deterministic structure for validation and demo; replace with LLM-driven JSON later.
        return {
            "decision": draft_decision,
            "rationale": [
                "Safety-first execution order",
                "Policy constraints satisfied",
            ],
            "assumptions": [
                "Target system is reachable",
                "No conflicting higher-priority tasks",
            ],
            "risks": [
                {
                    "risk": "Unintended side effects",
                    "severity": "MEDIUM",
                    "mitigation": "Require permit and execution guard",
                }
            ],
            "alternatives": [
                {
                    "option": "Request human approval",
                    "why_not": "Latency is acceptable for low-risk paths",
                }
            ],
        }
