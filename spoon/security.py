from fastapi import Header, HTTPException

from spoon.config import SETTINGS


def require_api_key(x_api_key: str = Header(default="")) -> None:
    if not SETTINGS.api_key:
        return
    if x_api_key != SETTINGS.api_key:
        raise HTTPException(status_code=401, detail="invalid api key")
