"""Generate SQL to set a user's password in auth_users. Use when login fails for an existing email.
   Run from backend root: python scripts/update_user_password.py <email> <password>
   Then run the printed SQL in Supabase → SQL Editor.
"""
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from auth_utils import hash_password


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/update_user_password.py <email> <password>")
        print("Example: python scripts/update_user_password.py student1@solstudy.com 'password123'")
        sys.exit(1)
    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    if not email or "@" not in email:
        print("Error: provide a valid email.")
        sys.exit(1)
    if len(password) < 6:
        print("Error: password must be at least 6 characters.")
        sys.exit(1)

    password_hash = hash_password(password)
    # Use parameter-style placeholder so user can copy-paste; hash may contain $
    print("Run this in Supabase → SQL Editor:")
    print()
    print(f"UPDATE public.auth_users SET password_hash = '{password_hash}' WHERE email = '{email}';")
    print()
    print("Then try logging in with that email and password.")


if __name__ == "__main__":
    main()
