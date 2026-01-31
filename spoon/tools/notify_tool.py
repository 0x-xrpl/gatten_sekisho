from typing import Any, Dict

from pydantic import Field
from spoon_ai.tools.base import BaseTool

from spoon.tools.storage_tool import StorageTool


class NotifyTool(BaseTool):
    name: str = "notify"
    description: str = "Notify result (stdout + log)"
    parameters: dict = {
        "type": "object",
        "properties": {
            "channel": {"type": "string"},
            "payload": {"type": "object"},
        },
        "required": ["channel", "payload"],
    }

    storage: StorageTool = Field(exclude=True)

    def __init__(self, storage: StorageTool, **kwargs: Any) -> None:
        super().__init__(storage=storage, **kwargs)

    def send(self, channel: str, payload: Dict[str, Any]) -> None:
        self.storage.append_jsonl("notifications.jsonl", {"channel": channel, **payload})

    async def execute(self, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.send(channel, payload)
        return {"notified": True}
