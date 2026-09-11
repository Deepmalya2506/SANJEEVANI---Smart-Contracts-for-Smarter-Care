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
    """Guarantees the core operational tables exist in Supabase PostgreSQL."""
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

    CREATE TABLE IF NOT EXISTS public.loans (
        loan_id UUID PRIMARY KEY,
        asset_id UUID,
        lender_hospital_id UUID,
        borrower_hospital_id UUID,
        loan_status TEXT NOT NULL DEFAULT 'REQUESTED',
        duration_hours INT DEFAULT 24,
        notes JSONB,
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_loans_lender ON public.loans (lender_hospital_id);
    CREATE INDEX IF NOT EXISTS idx_loans_borrower ON public.loans (borrower_hospital_id);

    CREATE TABLE IF NOT EXISTS public.loan_state_events (
        event_id UUID PRIMARY KEY,
        loan_id UUID,
        previous_state TEXT,
        new_state TEXT,
        actor_type TEXT,
        actor_id UUID,
        source TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS public.notifications (
        notification_id UUID PRIMARY KEY,
        hospital_id UUID,
        loan_id UUID,
        channel TEXT NOT NULL DEFAULT 'EMAIL',
        type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        attempt_count INT DEFAULT 1,
        provider_message_id TEXT,
        error_message TEXT,
        created_at TIMESTAMPTZ DEFAULT now(),
        sent_at TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS idx_notifications_hospital_id ON public.notifications (hospital_id);
    """
    try:
        with get_supabase_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(create_sql)
            connection.commit()
    except Exception as exc:
        # If Supabase credentials are not currently reachable, avoid crashing on startup
        print(f"[WARN] Could not ensure schema tables in Supabase: {exc}")
