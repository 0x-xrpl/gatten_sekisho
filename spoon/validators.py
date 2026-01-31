import json
from typing import Any, Dict, List, Optional


class ExplainValidationError(Exception):
    pass


def _require_list_str(value: Any, field: str) -> List[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise ExplainValidationError(f"{field} must be a non-empty list of strings")
    return value


def _validate_schema(payload: Dict[str, Any], schema_path: Optional[str]) -> None:
    if not schema_path:
        return
    try:
        import jsonschema  # type: ignore
    except Exception:
        return
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance=payload, schema=schema)


def validate_explain_payload(payload: Dict[str, Any], schema_path: Optional[str] = None) -> None:
    if not isinstance(payload, dict):
        raise ExplainValidationError("payload must be an object")

    for key in ["decision", "rationale", "assumptions", "risks", "alternatives"]:
        if key not in payload:
            raise ExplainValidationError(f"missing required field: {key}")

    if not isinstance(payload["decision"], str) or not payload["decision"].strip():
        raise ExplainValidationError("decision must be a non-empty string")

    _require_list_str(payload["rationale"], "rationale")
    _require_list_str(payload["assumptions"], "assumptions")

    risks = payload["risks"]
    if not isinstance(risks, list) or not risks:
        raise ExplainValidationError("risks must be a non-empty list")

    for risk in risks:
        if not isinstance(risk, dict):
            raise ExplainValidationError("risk entries must be objects")
        for key in ["risk", "severity", "mitigation"]:
            if key not in risk:
                raise ExplainValidationError(f"risk entry missing: {key}")
        if risk["severity"] not in {"LOW", "MEDIUM", "HIGH"}:
            raise ExplainValidationError("invalid severity value")
        if risk["severity"] == "HIGH" and not str(risk.get("mitigation", "")).strip():
            raise ExplainValidationError("HIGH severity requires mitigation")

    alternatives = payload["alternatives"]
    if not isinstance(alternatives, list) or not alternatives:
        raise ExplainValidationError("alternatives must be a non-empty list")
    for alt in alternatives:
        if not isinstance(alt, dict):
            raise ExplainValidationError("alternative entries must be objects")
        for key in ["option", "why_not"]:
            if key not in alt:
                raise ExplainValidationError(f"alternative entry missing: {key}")
        if not str(alt.get("option", "")).strip() or not str(alt.get("why_not", "")).strip():
            raise ExplainValidationError("alternative fields must be non-empty")

    _validate_schema(payload, schema_path)
