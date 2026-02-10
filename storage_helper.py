"""Upload files to Supabase Storage and return public URLs."""
import uuid

from fastapi import HTTPException
from storage3.utils import StorageException

from config import SUPABASE_TASK_BUCKET, SUPABASE_URL
from supabase_admin import get_supabase_admin

_bucket_ensured = False


def _ensure_task_bucket() -> None:
    """Create the task-files bucket if it does not exist (public for read URLs)."""
    global _bucket_ensured
    if _bucket_ensured:
        return
    supabase = get_supabase_admin()
    storage = supabase.storage
    try:
        storage.create_bucket(SUPABASE_TASK_BUCKET, options={"public": True})
    except StorageException as e:
        err = (e.args[0] or {}) if e.args else {}
        msg = str(err.get("message", "")).lower()
        code = err.get("statusCode")
        # Bucket already exists (e.g. created in Dashboard or by another process)
        if code in (400, 409) and ("already exists" in msg or "duplicate" in msg or "conflict" in msg):
            pass
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Storage bucket '{SUPABASE_TASK_BUCKET}' could not be created. Create it in Supabase Dashboard → Storage (set to Public), or check service role permissions.",
            ) from e
    _bucket_ensured = True


def _public_url(path: str) -> str:
    """Build public URL for a file in the task bucket."""
    base = SUPABASE_URL.rstrip("/")
    bucket = SUPABASE_TASK_BUCKET
    return f"{base}/storage/v1/object/public/{bucket}/{path}"


def _upload_task_attachment_once(
    file_data: bytes, path: str, content_type: str
) -> None:
    supabase = get_supabase_admin()
    supabase.storage.from_(SUPABASE_TASK_BUCKET).upload(
        path,
        file_data,
        file_options={"content-type": content_type or "application/octet-stream"},
    )


def _ascii_safe_storage_path(filename: str) -> str:
    """
    Build an ASCII-only path for Supabase Storage (rejects non-ASCII keys).
    Returns: attachments/{uuid}.{ext} with extension limited to ASCII alphanumeric.
    """
    ext = ""
    if "." in filename:
        raw_ext = filename.rsplit(".", 1)[-1]
        ext = "".join(c for c in raw_ext if c.isascii() and c.isalnum()).lower() or ""
    if not ext:
        ext = "bin"
    return f"attachments/{uuid.uuid4().hex}.{ext}"


def upload_task_attachment(
    file_data: bytes,
    filename: str,
    content_type: str,
) -> str:
    """
    Upload a mentor task attachment. Returns public URL.
    Storage path is ASCII-only (Supabase rejects non-ASCII keys). Original filename is kept in task attachments[].name.
    """
    global _bucket_ensured
    path = _ascii_safe_storage_path(filename)
    content_type = content_type or "application/octet-stream"
    _ensure_task_bucket()
    try:
        _upload_task_attachment_once(file_data, path, content_type)
    except StorageException as e:
        err = (e.args[0] or {}) if e.args else {}
        if err.get("message") == "Bucket not found":
            _bucket_ensured = False
            _ensure_task_bucket()
            _upload_task_attachment_once(file_data, path, content_type)
        else:
            raise
    return _public_url(path)


def _upload_submission_file_once(
    task_id: str, file_data: bytes, path: str, content_type: str
) -> None:
    supabase = get_supabase_admin()
    supabase.storage.from_(SUPABASE_TASK_BUCKET).upload(
        path,
        file_data,
        file_options={"content-type": content_type or "application/octet-stream"},
    )


def upload_submission_file(
    task_id: str,
    file_data: bytes,
    filename: str,
    content_type: str,
) -> str:
    """
    Upload a student submission file (image, etc.). Returns public URL.
    Storage path is ASCII-only (Supabase rejects non-ASCII keys).
    """
    global _bucket_ensured
    ext = ""
    if "." in filename:
        raw_ext = filename.rsplit(".", 1)[-1]
        ext = "".join(c for c in raw_ext if c.isascii() and c.isalnum()).lower() or ""
    path = f"submissions/{task_id}/{uuid.uuid4().hex}.{ext or 'bin'}"
    content_type = content_type or "application/octet-stream"
    _ensure_task_bucket()
    try:
        _upload_submission_file_once(task_id, file_data, path, content_type)
    except StorageException as e:
        err = (e.args[0] or {}) if e.args else {}
        if err.get("message") == "Bucket not found":
            _bucket_ensured = False
            _ensure_task_bucket()
            _upload_submission_file_once(task_id, file_data, path, content_type)
        else:
            raise
    return _public_url(path)
