"""Solstudy FastAPI backend. Uses Supabase (service role) and JWT_SECRET server-side only."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_router import router as auth_router
from feedback_router import router as feedback_router
from tasks_router import router as tasks_router
from supabase_admin import get_supabase_admin

app = FastAPI(
    title="Solstudy API",
    description="Backend for Solstudy (Supabase + JWT)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
