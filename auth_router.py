"""Custom auth: signup and login. Uses only the database (Supabase table auth_users).
   No Supabase Auth (no signInWithPassword, signUp, etc.). All auth is via this API + JWT."""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auth_utils import create_access_token, hash_password, verify_password
from config import JWT_PRIVATE_KEY
from supabase_admin import get_supabase_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

# Lenient email: at least one @ and something after it (for testing; tighten in production)
def is_valid_email(value: str) -> bool:
    return bool(value and "@" in value and len(value) > 3 and len(value) < 256)


class SignupBody(BaseModel):
    email: str
    password: str
    name: str | None = None
    role: str = "student"

    @property
    def role_normalized(self) -> str:
        return "mentor" if self.role == "mentor" else "student"


class LoginBody(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str


@router.post("/signup", response_model=AuthResponse)
def signup(body: SignupBody):
    if not JWT_PRIVATE_KEY:
        logger.error("Signup attempted but JWT_PRIVATE_KEY is not set (check server env)")
        raise HTTPException(
            status_code=503,
            detail="서버 설정이 완료되지 않았습니다. 관리자에게 문의하세요.",
        )
    if not is_valid_email(body.email):
        raise HTTPException(status_code=400, detail="이메일 형식이 올바르지 않습니다.")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="비밀번호는 6자 이상이어야 합니다.")

    supabase = get_supabase_admin()
    existing = (
        supabase.table("auth_users")
        .select("id")
        .eq("email", body.email.strip().lower())
        .execute()
    )
    if existing.data and len(existing.data) > 0:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다. 로그인해 주세요.")

    try:
        password_hash = hash_password(body.password)
    except Exception as e:
        logger.exception("Password hashing failed: %s", e)
        raise HTTPException(status_code=500, detail="회원가입에 실패했습니다.") from e

    role = body.role_normalized
    name = (body.name or "").strip() or body.email

    row = {
        "email": body.email.strip().lower(),
        "password_hash": password_hash,
        "name": name,
        "role": role,
    }
    try:
        # .select() is required so Supabase returns the inserted row in .data
        insert = (
            supabase.table("auth_users")
            .insert(row)
            .select("id, email, name, role")
            .execute()
        )
    except Exception as e:
        logger.exception("Supabase insert failed (auth_users): %s", e)
        raise HTTPException(status_code=500, detail="회원가입에 실패했습니다.") from e

    if insert.data and len(insert.data) > 0:
        user_row = insert.data[0]
    else:
        # Fallback: some Supabase setups don't return inserted row; fetch by email
        logger.info("auth_users insert returned no data, fetching by email for email=%s", body.email)
        fetch = (
            supabase.table("auth_users")
            .select("id, email, name, role")
            .eq("email", body.email.strip().lower())
            .limit(1)
            .execute()
        )
        if not fetch.data or len(fetch.data) == 0:
            logger.warning("auth_users insert succeeded but could not fetch row for email=%s", body.email)
            raise HTTPException(status_code=500, detail="회원가입에 실패했습니다.")
        user_row = fetch.data[0]
    user_id = str(user_row["id"])
    try:
        token = create_access_token(
            {"sub": user_id, "email": user_row["email"], "role": role}
        )
    except Exception as e:
        logger.exception("JWT creation failed on signup: %s", e)
        raise HTTPException(status_code=500, detail="회원가입에 실패했습니다.") from e

    return AuthResponse(
        user=UserResponse(
            id=user_id,
            email=user_row["email"],
            name=user_row.get("name") or user_row["email"],
            role=role,
        ),
        access_token=token,
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginBody):
    if not JWT_PRIVATE_KEY:
        logger.error("Login attempted but JWT_PRIVATE_KEY is not set (check server env)")
        raise HTTPException(
            status_code=503,
            detail="서버 설정이 완료되지 않았습니다. 관리자에게 문의하세요.",
        )
    supabase = get_supabase_admin()
    result = (
        supabase.table("auth_users")
        .select("id, email, name, role, password_hash")
        .eq("email", body.email.strip().lower())
        .execute()
    )
    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    row = result.data[0]
    stored_hash = row.get("password_hash")
    if not stored_hash:
        logger.warning("auth_users row missing password_hash for email=%s", body.email)
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    try:
        if not verify_password(body.password, stored_hash):
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    except (ValueError, TypeError) as e:
        logger.warning("Password verification failed (bad hash?): %s", e)
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    user_id = str(row["id"])
    role = "mentor" if row.get("role") == "mentor" else "student"
    try:
        token = create_access_token(
            {"sub": user_id, "email": row["email"], "role": role}
        )
    except ValueError as e:
        logger.error("JWT creation failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="서버 설정이 완료되지 않았습니다. 관리자에게 문의하세요.",
        ) from e
    return AuthResponse(
        user=UserResponse(
            id=user_id,
            email=row["email"],
            name=row.get("name") or row["email"],
            role=role,
        ),
        access_token=token,
    )


@router.get("/public-key")
def get_public_key():
    """Return the public key PEM for JWT verification (e.g. in frontend middleware)."""
    from config import JWT_PUBLIC_KEY
    if not JWT_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Public key not configured.")
    return {"public_key_pem": JWT_PUBLIC_KEY}
