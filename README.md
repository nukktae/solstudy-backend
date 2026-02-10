# Solstudy Backend (FastAPI)

- **Framework:** FastAPI
- **Auth:** Custom (signup/login with JWT RS256). Users stored in Supabase table `auth_users`.

## Env

Copy `.env.example` to `.env` and set:

- `SUPABASE_URL` – project URL
- `SUPABASE_SERVICE_ROLE_KEY` – server-only key (never expose to client)
- `JWT_PRIVATE_KEY` – RS256 private key PEM (for signing JWTs)
- `JWT_PUBLIC_KEY` – RS256 public key PEM (same as in frontend `NEXT_PUBLIC_JWT_PUBLIC_KEY`)

Generate keys:

```bash
pip install cryptography
python scripts/gen_jwt_keys.py
```

Paste the private key into `.env` as `JWT_PRIVATE_KEY` and the public key as `JWT_PUBLIC_KEY`. In `.env` you can use `\n` for newlines in the PEM, or put the key on one line. Put the same public key in the frontend `.env.local` as `NEXT_PUBLIC_JWT_PUBLIC_KEY`.

## Database (Supabase)

Run the migration once in Supabase SQL Editor (Dashboard → SQL Editor):

```sql
-- See supabase/migrations/20250210000000_create_auth_users.sql
create table if not exists public.auth_users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  name text,
  role text not null default 'student' check (role in ('student', 'mentor')),
  created_at timestamptz not null default now()
);
create index if not exists idx_auth_users_email on public.auth_users (email);
```

Then run the tasks migration (see `supabase/migrations/20250210100000_create_tasks_and_submissions.sql`) and the attachments migration (`20250210200000_add_task_attachments.sql`). Create a **public** Storage bucket named `task-files` in Supabase Dashboard → Storage (or set `SUPABASE_TASK_BUCKET` in `.env`) for mentor task attachments and student submission file uploads.

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
- **Start Command:** In the Start Command field put **only** this (no `startCommand:` or other prefix):
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```
  Do **not** use `app.main:app` — the app lives in `main.py`, not in an `app` package.
- Set env vars in Dashboard: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`, and optionally `SUPABASE_TASK_BUCKET`, `ALLOWED_ORIGINS`.
- **If login returns 500:** Ensure `JWT_PRIVATE_KEY` and `JWT_PUBLIC_KEY` are set on Render. Generate with `python scripts/gen_jwt_keys.py`, paste both into Render env (use `\n` for newlines in the PEM, or one line). The same public key must be in the frontend as `NEXT_PUBLIC_JWT_PUBLIC_KEY`.

## Auth endpoints

- `POST /api/auth/signup` – body: `{ "email", "password", "name?", "role?" }`
- `POST /api/auth/login` – body: `{ "email", "password" }`
- `GET /api/auth/public-key` – returns public key PEM (optional, for frontend)

## 과제 (Tasks) endpoints

All task endpoints require **Authorization: Bearer `<access_token>`** (from login).

- `GET /api/students` – **Mentor only.** List students (for task assignment).
- `POST /api/tasks` – **Mentor only.** Create task. **Form-data:** `title`, `subject`, `due_date`, `description`, `goal`, `student_id`; optional **files** (multiple file uploads). Attachments are stored in Supabase Storage and URLs saved on the task.
- `GET /api/tasks` – List tasks. Student: own only; optional `?due_date=`. Mentor: optional `?student_id=`.
- `GET /api/tasks/{task_id}` – Get one task.
- `POST /api/tasks/{task_id}/submit` – **Student only.** Submit task. **Form-data:** `study_time_minutes`; optional **files** (multiple file uploads). Uploaded files are stored in Supabase Storage and URLs saved on the submission.
