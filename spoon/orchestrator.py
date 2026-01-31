import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from spoon.agents.decision_agent import DecisionAgent
from spoon.agents.explain_agent import ExplainAgent
from spoon.audit import AuditLogger
from spoon.hashing import sha256_hex
from spoon.llm import SpoonLLM
from spoon.permit import PermitIssuer, PermitStore
from spoon.status import APPROVED, DENIED, ERROR, EXECUTED, HOLD, REJECTED
from spoon.tools.neo_tool import NeoTool
from spoon.tools.notify_tool import NotifyTool
from spoon.tools.policy_tool import PolicyTool
from spoon.tools.storage_tool import StorageTool
from spoon.validators import ExplainValidationError, validate_explain_payload


class Orchestrator:
    def __init__(self, policy_path: str, data_dir: str, explain_schema: str = "schemas/explain.schema.json") -> None:
        self.storage = StorageTool(base_dir=data_dir)
        self.audit_logger = AuditLogger(self.storage)
        self.policy_tool = PolicyTool(policy_path=policy_path)
        self.neo_tool = NeoTool(self.storage)
        self.notify_tool = NotifyTool(self.storage)
        self.permit_store = PermitStore(self.storage)
        self.permit_issuer = PermitIssuer(self.storage)
        self.explain_schema = explain_schema

        llm = SpoonLLM()
        self.decision_agent = DecisionAgent(llm)
        self.explain_agent = ExplainAgent(llm)

    def _explain_with_retries(self, user_request: str, draft_decision: str, context: Dict[str, Any]) -> Dict[str, Any]:
        last_error = None
        for _ in range(3):
            payload = self.explain_agent.run(user_request, draft_decision, context)
            try:
                validate_explain_payload(payload, schema_path=self.explain_schema)
                return payload
            except ExplainValidationError as exc:
                last_error = str(exc)
        raise ExplainValidationError(last_error or "explain validation failed")

    def _run_tool(self, tool, **kwargs: Any) -> Any:
        return asyncio.run(tool(**kwargs))

    def run(self, user_request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        decision = self.decision_agent.run(user_request, context, request_id=request_id)
        explain_payload: Dict[str, Any] = {}
        policy_result: Dict[str, Any] = {}
        status = ERROR
        reason: Optional[str] = None
        permit = None
        neo_result: Optional[Dict[str, Any]] = None

        try:
            explain_payload = self._explain_with_retries(
                user_request, decision["draft_decision"], context
            )
        except ExplainValidationError as exc:
            explain_payload = {
                "decision": decision["draft_decision"],
                "rationale": [],
                "assumptions": [],
                "risks": [{"risk": "invalid explain payload", "severity": "HIGH", "mitigation": ""}],
                "alternatives": [{"option": "manual review", "why_not": "validation failed"}],
            }
            policy_result = {
                "ok": False,
                "violations": [f"explain validation failed: {exc}"],
                "risk_level": "HIGH",
                "required_human_approval": False,
            }
            status = DENIED
            reason = f"explain validation failed: {exc}"
            permit = None
        else:
            try:
                policy_result = self._run_tool(
                    self.policy_tool,
                    decision=explain_payload["decision"],
                    context=context,
                )
            except Exception as exc:
                policy_result = {
                    "ok": False,
                    "violations": [f"policy tool error: {exc}"],
                    "risk_level": "HIGH",
                    "required_human_approval": False,
                }
                status = DENIED
                reason = f"policy tool error: {exc}"
            else:
                if policy_result["violations"]:
                    status = DENIED
                    reason = "; ".join(policy_result["violations"])
                elif policy_result["required_human_approval"]:
                    status = HOLD
                    reason = "human approval required"
                else:
                    permit_id = str(uuid.uuid4())
                    permit = self.permit_issuer.issue(
                        explain_payload=explain_payload,
                        policy_version=self.policy_tool.version,
                        risk_level=policy_result["risk_level"],
                        neo_tx_hash="PENDING",
                        permit_id=permit_id,
                        neo_mode="pending",
                    )
                    try:
                        neo_result = self._run_tool(
                            self.neo_tool,
                            permit_id=permit_id,
                            decision_hash=permit.decision_hash,
                            policy_version=self.policy_tool.version,
                            issued_at=int(permit.issued_at.timestamp()),
                            expires_at=int(permit.expires_at.timestamp()),
                        )
                    except Exception as exc:
                        status = HOLD
                        reason = f"neo write failed: {exc}"
                        permit = None
                        neo_result = {"tx_hash": None, "neo_mode": "error", "error": str(exc)}
                    else:
                        permit.neo_tx_hash = neo_result.get("tx_hash", "")
                        permit.neo_mode = neo_result.get("neo_mode", "mock")
                        self.permit_store.save(permit)
                        status = APPROVED

        notify_status = "SKIPPED"
        notify_error = None
        try:
            self._run_tool(self.notify_tool, channel="audit", payload={"request_id": request_id, "status": status})
            notify_status = "OK"
        except Exception as exc:
            notify_status = "FAILED"
            notify_error = str(exc)

        audit_record = {
            "request_id": request_id,
            "user_request": user_request,
            "context": context,
            "explain": explain_payload,
            "policy": policy_result,
            "status": status,
            "final_status": status,
            "reason": reason,
            "permit": permit.to_dict() if permit else None,
            "neo": neo_result,
            "notify_status": notify_status,
            "notify_error": notify_error,
        }
        self.audit_logger.append(audit_record)

        return {
            "request_id": request_id,
            "status": status,
            "reason": reason,
            "permit": permit.to_dict() if permit else None,
            "policy": policy_result,
            "explain": explain_payload,
            "neo": neo_result,
        }

    def execute(self, permit_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        audit_record = self.audit_logger.find_latest_by_permit_id(permit_id)
        if not audit_record or not audit_record.get("permit"):
            self.audit_logger.append(
                {
                    "action": "execute",
                    "permit_id": permit_id,
                    "status": REJECTED,
                    "final_status": REJECTED,
                    "reason": "permit not found",
                }
            )
            return {"ok": False, "status": REJECTED, "reason": "permit not found"}

        explain_payload = audit_record.get("explain") or {}
        permit = self.permit_store.get(permit_id)
        if permit is None:
            self.audit_logger.append(
                {
                    "action": "execute",
                    "permit_id": permit_id,
                    "status": REJECTED,
                    "final_status": REJECTED,
                    "reason": "permit not loaded",
                }
            )
            return {"ok": False, "status": REJECTED, "reason": "permit not loaded"}

        now = datetime.now(timezone.utc)
        if permit.expires_at <= now:
            self.audit_logger.append(
                {
                    "action": "execute",
                    "permit_id": permit_id,
                    "status": REJECTED,
                    "final_status": REJECTED,
                    "reason": "permit expired",
                }
            )
            return {"ok": False, "status": REJECTED, "reason": "permit expired"}

        expected_hash = sha256_hex(explain_payload)
        if permit.decision_hash != expected_hash:
            self.audit_logger.append(
                {
                    "action": "execute",
                    "permit_id": permit_id,
                    "status": REJECTED,
                    "final_status": REJECTED,
                    "reason": "decision hash mismatch",
                }
            )
            return {"ok": False, "status": REJECTED, "reason": "decision hash mismatch"}

        tool = action.get("tool")
        payload = action.get("payload", {})
        tool_result = None
        status = EXECUTED
        reason = None

        try:
            if tool == "neo_write":
                tool_result = self._run_tool(
                    self.neo_tool,
                    permit_id=permit.permit_id,
                    decision_hash=permit.decision_hash,
                    policy_version=permit.policy_version,
                    issued_at=int(permit.issued_at.timestamp()),
                    expires_at=int(permit.expires_at.timestamp()),
                )
            elif tool == "notify":
                tool_result = self._run_tool(self.notify_tool, **payload)
            elif tool == "storage":
                tool_result = self._run_tool(self.storage, **payload)
            else:
                status = REJECTED
                reason = "unknown tool"
        except Exception as exc:
            status = ERROR
            reason = f"execute tool failed: {exc}"

        audit_entry = {
            "action": "execute",
            "permit_id": permit_id,
            "final_status": status,
            "status": status,
            "reason": reason,
            "tool": tool,
            "tool_result": tool_result,
        }
        self.audit_logger.append(audit_entry)

        return {
            "ok": status == EXECUTED,
            "status": status,
            "reason": reason,
            "neo_tx_hash": tool_result.get("tx_hash") if isinstance(tool_result, dict) else None,
            "neo_mode": tool_result.get("neo_mode") if isinstance(tool_result, dict) else None,
        }
