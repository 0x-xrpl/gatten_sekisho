from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from spoon.config import SETTINGS
from spoon.orchestrator import Orchestrator
from spoon.security import require_api_key

router = APIRouter()

POLICY_PATH = SETTINGS.policy_path
DATA_DIR = SETTINGS.data_dir

orchestrator = Orchestrator(policy_path=POLICY_PATH, data_dir=DATA_DIR)


class SubmitRequest(BaseModel):
    user_request: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)


class ExecuteRequest(BaseModel):
    permit_id: str = Field(..., min_length=1)
    action: Dict[str, Any]


@router.post("/gate/submit", dependencies=[Depends(require_api_key)])
def gate_submit(payload: SubmitRequest) -> Dict[str, Any]:
    return orchestrator.run(user_request=payload.user_request, context=payload.context)


@router.post("/gate/execute", dependencies=[Depends(require_api_key)])
def gate_execute(payload: ExecuteRequest) -> Dict[str, Any]:
    result = orchestrator.execute(permit_id=payload.permit_id, action=payload.action)
    if result.get("status") == "REJECTED":
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=result.get("reason", "rejected"))
    return result
