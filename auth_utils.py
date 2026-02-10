"""Password hashing and JWT (RS256) for custom auth."""
from datetime import datetime, timezone, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from config import JWT_PRIVATE_KEY, JWT_PUBLIC_KEY

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "RS256"
JWT_EXPIRY_HOURS = 24 * 7  # 7 days


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_access_token(payload: dict[str, Any]) -> str:
    if not JWT_PRIVATE_KEY:
        raise ValueError("JWT_PRIVATE_KEY is not set")
    now = datetime.now(timezone.utc)
    payload = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRY_HOURS)).timestamp()),
    }
    return jwt.encode(
        payload,
        JWT_PRIVATE_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    if not JWT_PUBLIC_KEY:
        return None
    try:
        return jwt.decode(
            token,
            JWT_PUBLIC_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except Exception:
        return None
