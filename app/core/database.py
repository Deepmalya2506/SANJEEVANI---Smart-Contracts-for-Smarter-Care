import psycopg
from app.core.config import settings


def get_supabase_connection():
    return psycopg.connect(
        host=settings.SUPABASE_HOST,
        port=settings.SUPABASE_PORT,
        dbname=settings.SUPABASE_DATABASE,
        user=settings.SUPABASE_USER,
        password=settings.SUPABASE_PASSWORD,
        sslmode="require",
        connect_timeout=10,
    )