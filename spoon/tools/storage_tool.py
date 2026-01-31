import json
import os
from typing import Any, Dict

from spoon_ai.tools.base import BaseTool

from spoon.config import SETTINGS


class StorageTool(BaseTool):
    name: str = "audit_store"
    description: str = "Store audit logs locally"
    parameters: dict = {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "payload": {"type": "object"},
        },
        "required": ["filename", "payload"],
    }
    base_dir: str = SETTINGS.data_dir

    def __init__(self, base_dir: str = None, **kwargs: Any) -> None:
        if base_dir:
            kwargs["base_dir"] = base_dir
        super().__init__(**kwargs)
        os.makedirs(self.base_dir, exist_ok=True)

    def append_jsonl(self, filename: str, payload: Dict[str, Any]) -> None:
        path = os.path.join(self.base_dir, filename)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    async def execute(self, filename: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.append_jsonl(filename, payload)
        return {"stored": True}
