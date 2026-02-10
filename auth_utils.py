"""Verify Supabase Auth JWT (HS256). Payload includes sub, email, user_metadata (role, name)."""
from typing import Any

from jose import jwt

from config import SUPABASE_JWT_SECRET

SUPABASE_JWT_ALGORITHM = "HS256"


def decode_supabase_token(token: str) -> dict[str, Any] | None:
    """Verify Supabase access token and return normalized payload: sub, email, role, name."""
    if not SUPABASE_JWT_SECRET:
        return None
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[SUPABASE_JWT_ALGORITHM],
            audience="authenticated",
        )
    except Exception:
        return None
    if not payload or "sub" not in payload:
        return None
    # Normalize for app: role/name from user_metadata (set on signup)
    user_meta = payload.get("user_metadata") or {}
    role = user_meta.get("role") or "student"
    if role not in ("mentor", "student"):
        role = "student"
    name = user_meta.get("name") or payload.get("email") or ""
    return {
        "sub": payload["sub"],
        "email": payload.get("email") or "",
        "role": role,
        "name": name,
    }