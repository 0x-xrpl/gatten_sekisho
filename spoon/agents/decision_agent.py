from typing import Any, Dict

from spoon.llm import SpoonLLM


class DecisionAgent:
    def __init__(self, llm: SpoonLLM) -> None:
        self.llm = llm

    def run(self, user_request: str, context: Dict[str, Any], request_id: str = "") -> Dict[str, Any]:
        system = "You are a decision agent. Produce a concise actionable decision." \
                 "Return plain text only."
        prompt = f"Request: {user_request}\nContext: {context}"
        if request_id:
            self.llm.set_request_id(request_id)
        draft = self.llm.generate(system=system, user=prompt)
        return {
            "draft_decision": draft.strip(),
            "context": context,
        }
