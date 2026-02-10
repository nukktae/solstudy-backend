-- Daily feedback: mentor gives feedback per student per date (feedbackPerTask + dailySummary).
-- One row per (student_id, date). Payload matches frontend DailyFeedbackPayload.

create table if not exists public.feedback_daily (
  student_id uuid not null references public.auth_users(id) on delete cascade,
  date date not null,
  payload jsonb not null default '{"feedbackPerTask":[],"dailySummary":""}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (student_id, date)
);

create index if not exists idx_feedback_daily_student_id on public.feedback_daily (student_id);
create index if not exists idx_feedback_daily_date on public.feedback_daily (date);

comment on table public.feedback_daily is 'Mentor daily feedback per student: feedbackPerTask (taskId + items with content, isImportant) and dailySummary.';
