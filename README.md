# Solstudy Backend (FastAPI)

- **Framework:** FastAPI
- **Auth:** Supabase Auth. The frontend signs in/signs up via Supabase; the backend verifies the **Supabase access token** (JWT, HS256) and reads `sub`, `email`, `role`/`name` from the token. No custom signup/login endpoints.

## Env

**Where to get each value:** see [docs/CREDENTIALS.md](../docs/CREDENTIALS.md) for step-by-step instructions (Supabase Dashboard → Project Settings → API).

Copy `.env.example` to `.env` and set:

- `SUPABASE_URL` – project URL
- `SUPABASE_SERVICE_ROLE_KEY` – server-only key (never expose to client)
- `SUPABASE_JWT_SECRET` – from Supabase Dashboard → Project Settings → API → **JWT Secret**. Used to verify Supabase access tokens (HS256).

Optionally: `SUPABASE_TASK_BUCKET`, `ALLOWED_ORIGINS`.

## Database (Supabase)

1. Run migrations in Supabase SQL Editor (Dashboard → SQL Editor) in order:
   - `supabase/migrations/20250210000000_create_auth_users.sql`
   - `supabase/migrations/20250210100000_create_tasks_and_submissions.sql`
   - `supabase/migrations/20250210200000_add_task_attachments.sql`
   - `supabase/migrations/20250210300000_create_feedback_daily.sql`
   - `supabase/migrations/20250210400000_supabase_auth_profiles.sql` (profiles + trigger to sync new Supabase users into `auth_users`)

2. Create a **public** Storage bucket named `task-files` in Supabase Dashboard → Storage (or set `SUPABASE_TASK_BUCKET` in `.env`).

## Run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Deploy on Render

- **Root Directory:** `solstudy-back` (if deploying from monorepo).
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, and optionally `SUPABASE_TASK_BUCKET`, `ALLOWED_ORIGINS`.

## Auth

- **No signup/login on this backend.** The frontend uses Supabase Auth (`signInWithPassword`, `signUp`). Send the Supabase **access token** in `Authorization: Bearer <token>` for protected routes.
- `GET /api/auth/me` – returns current user (`id`, `email`, `name`, `role`) from the Bearer token. Requires valid Supabase JWT.

## 과제 (Tasks) endpoints

All require **Authorization: Bearer `<Supabase access_token>`**.

- `GET /api/students` – **Mentor only.** List students.
- `POST /api/tasks` – **Mentor only.** Create task (form-data + optional files).
- `GET /api/tasks` – List tasks (student: own; mentor: optional `?student_id=`).
- `GET /api/tasks/{task_id}` – Get one task.
- `POST /api/tasks/{task_id}/submit` – **Student only.** Submit task (form-data + optional files).
