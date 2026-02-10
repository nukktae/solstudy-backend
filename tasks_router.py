"""과제 (tasks) API: mentor creates tasks (with optional file uploads), student gets and submits (with optional file uploads)."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from auth_deps import get_current_user, require_mentor, require_student
from storage_helper import upload_submission_file, upload_task_attachment
from supabase_admin import get_supabase_admin

router = APIRouter(prefix="/api", tags=["tasks"])

SUBJECTS = {"korean", "math", "english"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_FILES_CREATE = 5
MAX_FILES_SUBMIT = 10


# --- Pydantic models (for JSON responses and optional JSON body) ---

class TaskAttachmentOut(BaseModel):
    name: str
    type: str
    size: int | None = None
    url: str | None = None

class TaskOut(BaseModel):
    id: str
    title: str
    subject: str
    due_date: str
    description: str | None
    goal: str | None
    student_id: str
    created_by: str | None = None
    created_at: str | None = None
    source: str = "mentor"
    attachments: list[TaskAttachmentOut] | None = None

# --- Helpers ---

def _row_to_task(row: dict) -> dict:
    due = row["due_date"]
    due_str = due.isoformat() if hasattr(due, "isoformat") else str(due)
    created_at = row.get("created_at")
    created_at_str = created_at.isoformat() if created_at and hasattr(created_at, "isoformat") else (str(created_at) if created_at else None)
    attachments = row.get("attachments")
    if attachments is None:
        attachments = []
    return {
        "id": str(row["id"]),
        "title": row["title"],
        "subject": row["subject"],
        "due_date": due_str,
        "description": row.get("description"),
        "goal": row.get("goal"),
        "student_id": str(row["student_id"]),
        "created_by": str(row["created_by"]) if row.get("created_by") else None,
        "created_at": created_at_str,
        "source": row.get("source") or "mentor",
        "attachments": attachments,
    }


# --- Mentor: create task (multipart: form fields + optional files) ---

@router.post("/tasks", response_model=TaskOut)
async def create_task(
    title: str = Form(...),
    subject: str = Form(...),
    due_date: str = Form(...),
    description: str = Form(""),
    goal: str = Form(""),
    student_id: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    current: dict = Depends(require_mentor),
    supabase=Depends(get_supabase_admin),
):
    """Create a 과제 (mentor only). Form fields + optional file uploads (attachments)."""
    if subject not in SUBJECTS:
        raise HTTPException(status_code=400, detail="subject must be korean, math, or english")
    if not title or not title.strip():
        raise HTTPException(status_code=400, detail="과제명을 입력해 주세요.")
    if len(files) > MAX_FILES_CREATE:
        raise HTTPException(status_code=400, detail=f"최대 {MAX_FILES_CREATE}개 파일만 첨부할 수 있습니다.")
    mentor_id = current["sub"]
    student_row = (
        supabase.table("auth_users")
        .select("id, role")
        .eq("id", student_id)
        .execute()
    )
    if not student_row.data or len(student_row.data) == 0:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    if student_row.data[0].get("role") != "student":
        raise HTTPException(status_code=400, detail="학생에게만 과제를 배정할 수 있습니다.")

    attachments: list[dict] = []
    for f in files:
        if not f.filename:
            continue
        data = await f.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"파일 크기는 {MAX_FILE_SIZE // (1024*1024)}MB 이하여야 합니다.")
        content_type = f.content_type or "application/octet-stream"
        url = upload_task_attachment(data, f.filename, content_type)
        attachments.append({"name": f.filename, "type": content_type, "size": len(data), "url": url})

    row = {
        "title": title.strip(),
        "subject": subject,
        "due_date": due_date,
        "description": description.strip() or None,
        "goal": goal.strip() or None,
        "student_id": student_id,
        "created_by": mentor_id,
        "source": "mentor",
        "attachments": attachments,
    }
    insert = supabase.table("tasks").insert(row).execute()
    if not insert.data or len(insert.data) == 0:
        raise HTTPException(status_code=500, detail="과제 생성에 실패했습니다.")
    return _row_to_task(insert.data[0])


# --- List students (mentor) ---

@router.get("/students")
def list_students(
    current: dict = Depends(require_mentor),
    supabase=Depends(get_supabase_admin),
):
    """List all students (mentor only). For dropdown when creating tasks."""
    r = (
        supabase.table("auth_users")
        .select("id, email, name")
        .eq("role", "student")
        .order("name")
        .execute()
    )
    return {
        "students": [
            {"id": str(x["id"]), "email": x["email"], "name": x.get("name") or x["email"]}
            for x in (r.data or [])
        ]
    }


# --- Student: list my tasks ---

@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    current: dict = Depends(get_current_user),
    due_date: str | None = Query(None, description="Filter by due_date YYYY-MM-DD"),
    student_id: str | None = Query(None, description="Mentor: filter by student_id"),
    supabase=Depends(get_supabase_admin),
):
    """List tasks. Student: only own tasks (optional due_date). Mentor: optional student_id filter."""
    user_id = current["sub"]
    role = current.get("role") or "student"
    cols = "id, title, subject, due_date, description, goal, student_id, created_by, created_at, source, attachments"
    if role == "student":
        q = supabase.table("tasks").select(cols).eq("student_id", user_id)
        if due_date:
            q = q.eq("due_date", due_date)
    else:
        q = supabase.table("tasks").select(cols)
        if student_id:
            q = q.eq("student_id", student_id)
    r = q.order("due_date").order("created_at").execute()
    return [_row_to_task(row) for row in (r.data or [])]


# --- Get single task ---

@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: str,
    current: dict = Depends(get_current_user),
    supabase=Depends(get_supabase_admin),
):
    """Get one task. Student: only own. Mentor: any."""
    user_id = current["sub"]
    role = current.get("role") or "student"
    r = supabase.table("tasks").select("*").eq("id", task_id).execute()
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    row = r.data[0]
    if role == "student" and str(row["student_id"]) != user_id:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    return _row_to_task(row)


# --- Student: submit task (multipart: form fields + optional files) ---

@router.post("/tasks/{task_id}/submit")
async def submit_task(
    task_id: str,
    study_time_minutes: int = Form(0),
    files: list[UploadFile] = File(default=[]),
    current: dict = Depends(require_student),
    supabase=Depends(get_supabase_admin),
):
    """Submit a 과제 (student only). Form: study_time_minutes + optional file uploads. One submission per task."""
    student_id = current["sub"]
    task_r = supabase.table("tasks").select("id, student_id").eq("id", task_id).execute()
    if not task_r.data or len(task_r.data) == 0:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    if str(task_r.data[0]["student_id"]) != student_id:
        raise HTTPException(status_code=403, detail="본인 과제만 제출할 수 있습니다.")
    existing = (
        supabase.table("task_submissions")
        .select("id")
        .eq("task_id", task_id)
        .eq("student_id", student_id)
        .execute()
    )
    if existing.data and len(existing.data) > 0:
        raise HTTPException(status_code=400, detail="이미 제출했습니다.")
    if len(files) > MAX_FILES_SUBMIT:
        raise HTTPException(status_code=400, detail=f"최대 {MAX_FILES_SUBMIT}개 파일만 첨부할 수 있습니다.")

    image_urls: list[str] = []
    for f in files:
        if not f.filename:
            continue
        data = await f.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"파일 크기는 {MAX_FILE_SIZE // (1024*1024)}MB 이하여야 합니다.")
        content_type = f.content_type or "application/octet-stream"
        url = upload_submission_file(task_id, data, f.filename, content_type)
        image_urls.append(url)

    row = {
        "task_id": task_id,
        "student_id": student_id,
        "study_time_minutes": max(0, study_time_minutes),
        "image_urls": image_urls,
    }
    insert = supabase.table("task_submissions").insert(row).execute()
    if not insert.data or len(insert.data) == 0:
        raise HTTPException(status_code=500, detail="제출에 실패했습니다.")
    sub = insert.data[0]
    submitted_at = sub.get("submitted_at")
    if submitted_at is not None and hasattr(submitted_at, "isoformat"):
        submitted_at = submitted_at.isoformat()
    return {
        "id": str(sub["id"]),
        "task_id": task_id,
        "submitted_at": submitted_at,
        "study_time_minutes": sub.get("study_time_minutes", 0),
        "image_urls": sub.get("image_urls") or [],
    }
