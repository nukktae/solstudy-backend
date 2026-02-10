-- Add attachments to tasks (mentor-uploaded files: PDFs, images, etc.)
alter table public.tasks
  add column if not exists attachments jsonb not null default '[]'::jsonb;

comment on column public.tasks.attachments is 'Array of { name, type, size?, url } for mentor-uploaded files.';
