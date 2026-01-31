import json
import os

POLICY = {
    "version": "v1.0",
    "rules": [
        {
            "id": "no_pii",
            "type": "blocklist",
            "patterns": ["ssn", "password", "credit card", "private key"],
            "message": "PII or secrets are not allowed",
        },
        {
            "id": "no_destructive",
            "type": "blocklist",
            "patterns": ["delete", "drop", "rm -rf"],
            "message": "destructive operations are blocked",
        },
        {
            "id": "high_value_transfer",
            "type": "require_approval",
            "patterns": ["transfer", "send", "withdraw"],
            "message": "high value transfer requires human approval",
        },
    ],
    "registered_tools": ["policy_check", "audit_store", "neo_write", "notify", "execution_guard"],
}


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "policies", "policy.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(POLICY, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
