"""Supabase Auth: no custom signup/login. Frontend uses Supabase client.
   This router provides GET /api/auth/me for current user from Bearer token."""
from fastapi import APIRouter, Depends

from auth_deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me")
def me(current: dict = Depends(get_current_user)):
    """Return current user from Supabase JWT (sub, email, role, name)."""
    return {
        "id": current["sub"],
        "email": current.get("email") or "",
        "name": current.get("name") or current.get("email") or "",
        "role": current.get("role") or "student",
    }