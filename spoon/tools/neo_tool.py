import os
import re
import shutil
import subprocess
import time
from typing import Any, Dict, Optional

from pydantic import Field
from spoon_ai.tools.base import BaseTool

from spoon.config import SETTINGS
from spoon.tools.storage_tool import StorageTool


class NeoToolError(RuntimeError):
    pass


class NeoTool(BaseTool):
    name: str = "neo_write"
    description: str = "Write permit hash to local Neo Express chain (mock by default)"
    parameters: dict = {
        "type": "object",
        "properties": {
            "permit_id": {"type": "string"},
            "decision_hash": {"type": "string"},
            "policy_version": {"type": "string"},
            "issued_at": {"type": "integer"},
            "expires_at": {"type": "integer"},
        },
        "required": ["permit_id", "decision_hash", "policy_version", "issued_at", "expires_at"],
    }
    simulate: bool = True
    storage: StorageTool = Field(exclude=True)

    def __init__(self, storage: StorageTool, **kwargs: Any) -> None:
        super().__init__(storage=storage, **kwargs)
        self.simulate = True

    def _write_simulated(
        self,
        permit_id: str,
        decision_hash: str,
        policy_version: str,
        issued_at: int,
        expires_at: int,
    ) -> Dict[str, Any]:
        tx_hash = f"MOCK_TX_{permit_id.replace('-', '')[:24]}"
        record = {
            "permit_id": permit_id,
            "decision_hash": decision_hash,
            "policy_version": policy_version,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "tx_hash": tx_hash,
            "timestamp": int(time.time()),
            "mode": "mock",
        }
        self.storage.append_jsonl("neo_tx.jsonl", record)
        return {"tx_hash": tx_hash, "neo_mode": "mock", "rpc_url": SETTINGS.neo_rpc_url}

    def _extract_tx_hash(self, text: str) -> Optional[str]:
        match = re.search(r"0x[a-fA-F0-9]{64}", text)
        return match.group(0) if match else None

    def _write_real(
        self,
        permit_id: str,
        decision_hash: str,
        policy_version: str,
        issued_at: int,
        expires_at: int,
    ) -> Dict[str, Any]:
        cmd = os.getenv("NEO_EXPRESS_CMD", "neoxp")
        if not shutil.which(cmd):
            raise NeoToolError("neoxp CLI not found (install Neo Express)")

        if SETTINGS.neo_simulate:
            raise NeoToolError("NEO_SIMULATE=1 set; refusing real tx")

        if not SETTINGS.neo_rpc_url or not SETTINGS.neo_wif or not SETTINGS.neo_contract_hash:
            raise NeoToolError("missing NEO_RPC_URL / NEO_WIF / NEO_CONTRACT_HASH")

        decision_hash_hex = decision_hash if decision_hash.startswith("0x") else f"0x{decision_hash}"
        args = [
            cmd,
            "contract",
            "invoke",
            "--rpc",
            SETTINGS.neo_rpc_url,
            "--wif",
            SETTINGS.neo_wif,
            "--hash",
            SETTINGS.neo_contract_hash,
            "--method",
            "register_permit",
            "--arg",
            permit_id,
            "--arg",
            decision_hash_hex,
            "--arg",
            str(issued_at),
            "--arg",
            str(expires_at),
            "--arg",
            policy_version,
        ]

        result = subprocess.run(args, capture_output=True, text=True)
        output = "\n".join([result.stdout, result.stderr])
        if result.returncode != 0:
            raise NeoToolError(f"neoxp invoke failed: {output.strip()}")

        tx_hash = self._extract_tx_hash(output)
        if not tx_hash:
            raise NeoToolError(f"tx hash not found in output: {output.strip()}")

        record = {
            "permit_id": permit_id,
            "decision_hash": decision_hash,
            "policy_version": policy_version,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "tx_hash": tx_hash,
            "timestamp": int(time.time()),
            "mode": "real",
            "rpc_url": SETTINGS.neo_rpc_url,
        }
        self.storage.append_jsonl("neo_tx.jsonl", record)
        return {"tx_hash": tx_hash, "neo_mode": "real", "rpc_url": SETTINGS.neo_rpc_url}

    async def execute(
        self,
        permit_id: str,
        decision_hash: str,
        policy_version: str,
        issued_at: int,
        expires_at: int,
    ) -> Dict[str, Any]:
        if SETTINGS.neo_rpc_url and SETTINGS.neo_wif and SETTINGS.neo_contract_hash and not SETTINGS.neo_simulate:
            return self._write_real(permit_id, decision_hash, policy_version, issued_at, expires_at)
        return self._write_simulated(permit_id, decision_hash, policy_version, issued_at, expires_at)
