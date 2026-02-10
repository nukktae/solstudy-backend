"""Solstudy FastAPI backend. Uses Supabase (service role) and JWT_SECRET server-side only."""
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_router import router as auth_router
from feedback_router import router as feedback_router
from tasks_router import router as tasks_router
from supabase_admin import get_supabase_admin
from config import CORS_ORIGINS

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Solstudy API",
    description="Backend for Solstudy (Supabase + JWT)",
    version="0.1.0",
)


def _add_cors_to_response(response: Response, request: Request) -> None:
    """Set CORS headers on response if request has an allowed origin."""
    origin = request.headers.get("origin")
    if origin and origin in CORS_ORIGINS:
        response.headers.setdefault("Access-Control-Allow-Origin", origin)
        response.headers.setdefault("Access-Control-Allow-Credentials", "true")


class EnsureCORSHeadersMiddleware(BaseHTTPMiddleware):
    """Ensure CORS headers are on every response (including 4xx/5xx and unhandled errors)."""
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception("Unhandled exception: %s", e)
            response = JSONResponse(
                status_code=500,
                content={"detail": "서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."},
            )
        _add_cors_to_response(response, request)
        return response


# Order: last added runs first. EnsureCORS runs first so it runs last on response (adds headers if missing).
app.add_middleware(EnsureCORSHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(feedback_router)
app.include_router(tasks_router)


@app.get("/")
def root():
    return {"service": "solstudy-back", "status": "ok"}


@app.get("/health")
def health():
    return {"ok": True}


# Example: use Supabase admin (e.g. in a protected route)
@app.get("/api/demo")
def demo():
    """Example endpoint; replace with real logic."""
    # Ensure env is loaded and service role is not exposed
    _ = get_supabase_admin()
    return {"message": "Backend is using Supabase (service role) and JWT_SECRET server-side only."}
