import asyncio
import os
import sys
from pathlib import Path
from typing import Optional
import threading
import logging
from concurrent.futures import Future

from spoon.config import SETTINGS

ROOT = Path(__file__).resolve().parents[1]
SPOON_CORE = ROOT / "spoon-core"
if str(SPOON_CORE) not in sys.path:
    sys.path.insert(0, str(SPOON_CORE))

from spoon_ai.schema import Message  # type: ignore
from spoon_ai.llm.providers.ollama_provider import OllamaProvider  # type: ignore


class SpoonLLM:
    """SpoonOS unified LLM adapter using local Ollama via spoon-core."""

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or os.getenv("OLLAMA_MODEL", "tinyllama")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "30"))
        self._provider = None
        self._initialized = False
        self._loop = None
        self._thread = None
        self._start_loop()

    def _start_loop(self) -> None:
        if self._loop is not None:
            return

        def _run_loop(loop: asyncio.AbstractEventLoop) -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=_run_loop, args=(loop,), daemon=True)
        thread.start()
        self._loop = loop
        self._thread = thread

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._provider = OllamaProvider()
        await self._provider.initialize(
            {
                "api_key": "ollama",
                "model": self.model,
                "base_url": self.base_url,
                "timeout": self.timeout,
            }
        )
        self._initialized = True

    async def _chat(self, system: str, user: str) -> str:
        await self._ensure_initialized()
        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]
        response = await self._provider.chat(messages)
        await self._provider.cleanup()
        self._initialized = False
        return response.content

    def generate(self, system: str, user: str) -> str:
        if self._loop is None:
            self._start_loop()
        logger = logging.getLogger("gatten_gate.llm")
        logger.info(
            "LLM_CALL: Agent -> SpoonOS(llm.py) -> Ollama request_id=%s model=%s",
            getattr(self, "_request_id", "n/a"),
            self.model,
        )
        future: Future = asyncio.run_coroutine_threadsafe(self._chat(system, user), self._loop)  # type: ignore[arg-type]
        result = future.result()
        self._request_id = "n/a"
        return result

    def set_request_id(self, request_id: str) -> None:
        self._request_id = request_id
