import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    policy_path: str = os.getenv("POLICY_PATH", "policies/policy.json")
    data_dir: str = os.getenv("DATA_DIR", "data")
    api_key: str = os.getenv("GATTEN_API_KEY", "")

    spoonos_base_url: str = os.getenv("SPOONOS_BASE_URL", "")
    spoonos_api_key: str = os.getenv("SPOONOS_API_KEY", "")
    spoonos_model: str = os.getenv("SPOONOS_LLM_MODEL", "")
    spoonos_timeout: int = int(os.getenv("SPOONOS_TIMEOUT", "30"))

    neo_rpc_url: str = os.getenv("NEO_RPC_URL", "")
    neo_wif: str = os.getenv("NEO_WIF", "")
    neo_contract_hash: str = os.getenv("NEO_CONTRACT_HASH", "")
    neo_network: str = os.getenv("NEO_NETWORK", "testnet")
    neo_tx_timeout: int = int(os.getenv("NEO_TX_TIMEOUT", "30"))
    neo_simulate: bool = os.getenv("NEO_SIMULATE", "0") == "1"

    audit_hmac_secret: str = os.getenv("AUDIT_HMAC_SECRET", "")
    audit_allow_unsigned: bool = os.getenv("AUDIT_ALLOW_UNSIGNED", "0") == "1"

    strict_mode: bool = os.getenv("GATTEN_STRICT", "1") == "1"


SETTINGS = Settings()
