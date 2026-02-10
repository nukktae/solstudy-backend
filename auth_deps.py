"""FastAPI dependencies: get current user from JWT Bearer token."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth_utils import decode_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Require valid JWT; return payload with sub (user id), email, role."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return payload


def require_mentor(current: dict = Depends(get_current_user)) -> dict:
    """Require current user to be mentor."""
    if current.get("role") != "mentor":
        raise HTTPException(status_code=403, detail="멘토만 이용할 수 있습니다.")
    return current


def require_student(current: dict = Depends(get_current_user)) -> dict:
    """Require current user to be student."""
    if current.get("role") != "student":
        raise HTTPException(status_code=403, detail="학생만 이용할 수 있습니다.")
    return current
