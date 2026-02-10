-- Custom auth: users stored in Supabase. Run this in Supabase SQL Editor (Dashboard -> SQL Editor).
create table if not exists public.auth_users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  name text,
  role text not null default 'student' check (role in ('student', 'mentor')),
  created_at timestamptz not null default now()
);

create index if not exists idx_auth_users_email on public.auth_users (email);

comment on table public.auth_users is 'Custom auth users (replaces Supabase Auth for this app).';
