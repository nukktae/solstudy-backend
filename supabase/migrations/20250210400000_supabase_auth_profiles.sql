-- Supabase Auth: profiles for role/name and sync to auth_users so existing task/feedback FKs work.
-- Run in Supabase SQL Editor (Dashboard → SQL Editor).

-- App profiles (id = auth.users.id). Used for role/name in JWT user_metadata and optional RLS.
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text,
  role text not null default 'student' check (role in ('student', 'mentor')),
  created_at timestamptz not null default now()
);

comment on table public.profiles is 'App profile per Supabase Auth user (name, role). Synced from user_metadata on signup.';

-- Sync new Supabase Auth users into auth_users so tasks/task_submissions/feedback_daily FKs (auth_users.id) still resolve.
-- password_hash is set to empty; these users sign in via Supabase only.
create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, name, role)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', new.email),
    coalesce(nullif(trim(new.raw_user_meta_data->>'role'), ''), 'student')
  );
  insert into public.auth_users (id, email, password_hash, name, role)
  select
    new.id,
    new.email,
    '.',
    coalesce(new.raw_user_meta_data->>'name', new.email),
    coalesce(nullif(trim(new.raw_user_meta_data->>'role'), ''), 'student')
  where not exists (select 1 from public.auth_users where email = new.email);
  return new;
end;
$$;

-- auth_users.id must exist and be unique; if your table uses id uuid default gen_random_uuid(), add unique(id) or ensure id is primary key.
-- Trigger on auth.users (Supabase managed).
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_auth_user();
