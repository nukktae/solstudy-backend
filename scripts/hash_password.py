"""Print bcrypt hash for a password. Use to fix auth_users.password_hash if you inserted users without hashing.
   Run from backend root: python scripts/hash_password.py [password]
   Default password: password123
   Then in Supabase SQL Editor:
     UPDATE public.auth_users SET password_hash = '<paste_hash_here>' WHERE email = 'student1@solstudy.com';
"""
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from auth_utils import hash_password

def main():
    password = (sys.argv[1] if len(sys.argv) > 1 else "password123").strip()
    if not password:
        print("Usage: python scripts/hash_password.py [password]")
        sys.exit(1)
    h = hash_password(password)
    print("Use this hash in Supabase (Table Editor or SQL):")
    print(h)
    print()
    print("Example SQL (replace <hash> and email as needed):")
    print("  UPDATE public.auth_users SET password_hash = '<hash>' WHERE email = 'student1@solstudy.com';")

if __name__ == "__main__":
    main()
