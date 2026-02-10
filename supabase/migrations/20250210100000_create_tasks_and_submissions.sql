-- 과제 (tasks) and 제출 (task_submissions). Run in Supabase SQL Editor.
-- Tasks are created by mentors and assigned to students; students submit.

create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  subject text not null check (subject in ('korean', 'math', 'english')),
  due_date date not null,
  description text,
  goal text,
  student_id uuid not null references public.auth_users(id) on delete cascade,
  created_by uuid not null references public.auth_users(id) on delete cascade,
  source text not null default 'mentor' check (source in ('mentor', 'student')),
  created_at timestamptz not null default now()
);

create index if not exists idx_tasks_student_id on public.tasks (student_id);
create index if not exists idx_tasks_due_date on public.tasks (due_date);
create index if not exists idx_tasks_created_by on public.tasks (created_by);

create table if not exists public.task_submissions (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.tasks(id) on delete cascade,
  student_id uuid not null references public.auth_users(id) on delete cascade,
  submitted_at timestamptz not null default now(),
  study_time_minutes int not null default 0 check (study_time_minutes >= 0),
  image_urls jsonb not null default '[]'::jsonb
);

create unique index if not exists idx_task_submissions_one_per_task_student
  on public.task_submissions (task_id, student_id);
create index if not exists idx_task_submissions_student_id on public.task_submissions (student_id);
create index if not exists idx_task_submissions_task_id on public.task_submissions (task_id);

comment on table public.tasks is '과제: mentor-created or student self-added.';
comment on table public.task_submissions is '과제 제출: one submission per task per student.';
