"""List users in auth_users. Run from backend root: python scripts/check_users.py"""
import sys
from pathlib import Path

# Ensure backend root is on path so config and supabase_admin load
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from supabase_admin import get_supabase_admin

def main():
    supabase = get_supabase_admin()
    result = supabase.table("auth_users").select("id, email, name, role, created_at").order("created_at", desc=True).execute()
    rows = result.data or []
    print(f"Users in auth_users: {len(rows)}")
    for r in rows:
        print(f"  - {r.get('email')} | {r.get('name')} | {r.get('role')} | id={r.get('id')}")
    if not rows:
        print("  (none – sign up once on production or insert via Supabase SQL)")

if __name__ == "__main__":
    main()
