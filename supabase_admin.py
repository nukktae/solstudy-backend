"""Supabase admin client (service role). Server-only."""
from supabase import create_client

from config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL

_admin_client = None


def get_supabase_admin():
    """Singleton Supabase client with service role. Use only on the server."""
    global _admin_client
    if _admin_client is None:
        _admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _admin_client
