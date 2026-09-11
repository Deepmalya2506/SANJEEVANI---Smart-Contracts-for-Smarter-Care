# pyrefly: ignore [missing-import]
import psycopg
from app.core.config import settings


def get_supabase_connection():
    """Returns a direct PostgreSQL connection to Supabase via psycopg."""
    host = settings.SUPABASE_HOST.strip() or "127.0.0.1"
    sslmode = "prefer" if host in ("127.0.0.1", "localhost", "") else "require"
    return psycopg.connect(
        host=host,
        port=settings.SUPABASE_PORT,
        dbname=settings.SUPABASE_DATABASE,
        user=settings.SUPABASE_USER,
        password=settings.SUPABASE_PASSWORD,
        sslmode=sslmode,
        connect_timeout=5,
    )


def ensure_payments_table_exists():
    """Guarantees the public.payments table exists in Supabase PostgreSQL."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS public.payments (
        payment_id UUID PRIMARY KEY,
        order_id TEXT UNIQUE NOT NULL,
        payment_provider_id TEXT,
        loan_reference TEXT,
        amount_paise BIGINT NOT NULL,
        amount_rupees NUMERIC NOT NULL,
        currency TEXT NOT NULL DEFAULT 'INR',
        status TEXT NOT NULL DEFAULT 'PAYMENT_PENDING',
        receipt TEXT,
        signature TEXT,
        notes JSONB,
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_payments_order_id ON public.payments (order_id);
    CREATE INDEX IF NOT EXISTS idx_payments_status ON public.payments (status);
    """
    try:
        with get_supabase_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(create_sql)
            connection.commit()
    except Exception as exc:
        # If Supabase credentials are not currently reachable, avoid crashing on startup
        print(f"[WARN] Could not ensure payments table in Supabase: {exc}")
