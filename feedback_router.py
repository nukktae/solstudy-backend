"""Feedback API: mentor creates/updates daily feedback; mentor and student get feedback by date."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query

from auth_deps import require_mentor, require_student
from pydantic import BaseModel, Field
from supabase_admin import get_supabase_admin

router = APIRouter(prefix="/api", tags=["feedback"])


# --- Pydantic models (align with frontend FeedbackItem, FeedbackPerTask, DailyFeedbackPayload) ---

class FeedbackItemIn(BaseModel):
    content: str = ""
    is_important: bool = Field(False, alias="isImportant")

    class Config:
        populate_by_name = True


class FeedbackPerTaskIn(BaseModel):
    task_id: str = Field(..., alias="taskId")
    items: list[FeedbackItemIn] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class DailyFeedbackPayloadIn(BaseModel):
    feedback_per_task: list[FeedbackPerTaskIn] = Field(default_factory=list, alias="feedbackPerTask")
    daily_summary: str = Field("", alias="dailySummary")

    class Config:
        populate_by_name = True


# Response: same shape as frontend (camelCase for feedbackPerTask, dailySummary)
class FeedbackItemOut(BaseModel):
    content: str
    isImportant: bool = False


class FeedbackPerTaskOut(BaseModel):
    taskId: str
    items: list[FeedbackItemOut] = []


class DailyFeedbackPayloadOut(BaseModel):
    feedbackPerTask: list[FeedbackPerTaskOut] = []
    dailySummary: str = ""


def _normalize_payload(payload: dict) -> dict:
    """Ensure payload has feedbackPerTask (list) and dailySummary (str)."""
    if not isinstance(payload, dict):
        return {"feedbackPerTask": [], "dailySummary": ""}
    ft = payload.get("feedbackPerTask")
    if not isinstance(ft, list):
        ft = []
    ds = payload.get("dailySummary")
    if not isinstance(ds, str):
        ds = ""
    return {"feedbackPerTask": ft, "dailySummary": ds}


def _row_to_payload(row: dict) -> DailyFeedbackPayloadOut:
    payload = _normalize_payload(row.get("payload") or {})
    feedback_per_task = []
    for fp in payload.get("feedbackPerTask") or []:
        task_id = fp.get("taskId") or str(fp.get("task_id", ""))
        items = []
        for it in fp.get("items") or []:
            items.append(FeedbackItemOut(
                content=it.get("content") or "",
                isImportant=bool(it.get("isImportant", it.get("is_important", False))),
            ))
        feedback_per_task.append(FeedbackPerTaskOut(taskId=task_id, items=items))
    return DailyFeedbackPayloadOut(
        feedbackPerTask=feedback_per_task,
        dailySummary=payload.get("dailySummary") or "",
    )


def _body_to_payload(body: DailyFeedbackPayloadIn) -> dict:
    ft = []
    for fp in body.feedback_per_task:
        items = [{"content": it.content, "isImportant": it.is_important} for it in fp.items]
        ft.append({"taskId": fp.task_id, "items": items})
    return {"feedbackPerTask": ft, "dailySummary": body.daily_summary}


# --- Mentor: create or update daily feedback for a student ---

@router.put("/feedback", response_model=DailyFeedbackPayloadOut)
def upsert_feedback(
    body: DailyFeedbackPayloadIn,
    student_id: str = Query(..., description="Student ID"),
    date: str = Query(..., description="Date YYYY-MM-DD"),
    current: dict = Depends(require_mentor),
    supabase=Depends(get_supabase_admin),
):
    """Mentor only. Create or update daily feedback for a student. One record per (student_id, date)."""
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    # Ensure student exists and is a student
    user_r = (
        supabase.table("auth_users")
        .select("id, role")
        .eq("id", student_id)
        .execute()
    )
    if not user_r.data or len(user_r.data) == 0:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    if user_r.data[0].get("role") != "student":
        raise HTTPException(status_code=400, detail="학생에게만 피드백을 남길 수 있습니다.")

    payload = _body_to_payload(body)
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    row = {
        "student_id": student_id,
        "date": date,
        "payload": payload,
        "updated_at": now_iso,
    }
    r = (
        supabase.table("feedback_daily")
        .upsert(row, on_conflict="student_id,date")
        .execute()
    )
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=500, detail="피드백 저장에 실패했습니다.")
    return _row_to_payload(r.data[0])


# --- Mentor: get daily feedback for a student ---

@router.get("/feedback", response_model=DailyFeedbackPayloadOut | None)
def get_feedback_mentor(
    student_id: str = Query(..., description="Student ID"),
    date: str = Query(..., description="Date YYYY-MM-DD"),
    current: dict = Depends(require_mentor),
    supabase=Depends(get_supabase_admin),
):
    """Mentor only. Get daily feedback for a student. Returns null if none saved."""
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    r = (
        supabase.table("feedback_daily")
        .select("*")
        .eq("student_id", student_id)
        .eq("date", date)
        .execute()
    )
    if not r.data or len(r.data) == 0:
        return None
    return _row_to_payload(r.data[0])


# --- Student: get my daily feedback for a date ---

@router.get("/feedback/me", response_model=DailyFeedbackPayloadOut | None)
def get_feedback_student(
    date: str = Query(..., description="Date YYYY-MM-DD"),
    current: dict = Depends(require_student),
    supabase=Depends(get_supabase_admin),
):
    """Student only. Get my daily feedback for a date. Returns null if none."""
    student_id = current["sub"]
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    r = (
        supabase.table("feedback_daily")
        .select("*")
        .eq("student_id", student_id)
        .eq("date", date)
        .execute()
    )
    if not r.data or len(r.data) == 0:
        return None
    return _row_to_payload(r.data[0])
