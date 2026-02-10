"""Load server-only env. Never use these values in the frontend."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend root
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
# Bucket for task attachments (mentor) and submission files (student). Create in Dashboard → Storage.
SUPABASE_TASK_BUCKET: str = os.environ.get("SUPABASE_TASK_BUCKET", "task-files")
# Optional until you add JWT verification for protected routes. Set in .env for production.
JWT_SECRET: str = os.environ.get("JWT_SECRET", "")

# Custom auth: RS256 JWT. Generate with: python -m solstudy_back.gen_keys (or see README).
JWT_PRIVATE_KEY: str = os.environ.get("JWT_PRIVATE_KEY", "").replace("\\n", "\n")
JWT_PUBLIC_KEY: str = os.environ.get("JWT_PUBLIC_KEY", "").replace("\\n", "\n")

# CORS: comma-separated origins. Default includes localhost + production frontend.
_DEFAULT_ORIGINS = "http://localhost:3000,https://solstudy.vercel.app"
_ALLOWED = os.environ.get("ALLOWED_ORIGINS", _DEFAULT_ORIGINS).strip()
CORS_ORIGINS: list[str] = [o.strip() for o in _ALLOWED.split(",") if o.strip()]
if not CORS_ORIGINS:
    CORS_ORIGINS = ["http://localhost:3000", "https://solstudy.vercel.app"]
