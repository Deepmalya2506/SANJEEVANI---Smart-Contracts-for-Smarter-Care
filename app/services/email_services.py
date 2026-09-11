import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID, uuid4

from psycopg.rows import dict_row

from app.core.config import settings
from app.core.database import get_supabase_connection


def _ensure_notifications_table(cursor):
    cursor.execute(
        """
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
    )


def send_transactional_notification(
    hospital_id: UUID | str | None,
    recipient_email: str,
    event_type: str,
    subject: str,
    html_content: str,
    loan_id: UUID | str | None = None,
) -> None:
    notification_id = uuid4()
    h_uuid = None
    if hospital_id:
        try:
            h_uuid = UUID(str(hospital_id))
        except (ValueError, AttributeError):
            h_uuid = None

    l_uuid = None
    if loan_id:
        try:
            l_uuid = UUID(str(loan_id))
        except (ValueError, AttributeError):
            l_uuid = None

    # 1. Initialize notification ledger entry as PENDING
    db_available = False
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                _ensure_notifications_table(cursor)
                cursor.execute(
                    """
                    INSERT INTO public.notifications (
                        notification_id, hospital_id, loan_id, channel, type, status, attempt_count
                    )
                    VALUES (%s, %s, %s, 'EMAIL', %s, 'PENDING', 1)
                    """,
                    (notification_id, h_uuid, l_uuid, event_type),
                )
                connection.commit()
                db_available = True
    except Exception as exc:
        print(f"[WARN] Supabase notifications table unavailable: {exc}")

    # If SMTP credentials are missing, mark as SKIPPED and exit
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        if db_available:
            try:
                with get_supabase_connection() as connection:
                    with connection.cursor(row_factory=dict_row) as cursor:
                        cursor.execute(
                            """
                            UPDATE public.notifications
                            SET status = 'SKIPPED', error_message = 'SMTP credentials not configured in environment.'
                            WHERE notification_id = %s
                            """,
                            (notification_id,),
                        )
                        connection.commit()
            except Exception:
                pass
        return

    # 2. Build MIME Email Message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = recipient_email
    message.attach(MIMEText(html_content, "html"))

    # 3. Transmit via SMTP
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, [recipient_email], message.as_string())

        # 4. Mark notification as SENT
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    UPDATE public.notifications
                    SET 
                        status = 'SENT',
                        sent_at = now(),
                        provider_message_id = %s
                    WHERE notification_id = %s
                    """,
                    (f"smtp-{uuid4()}", notification_id),
                )
                connection.commit()

    except Exception as exc:
        print(f"[ERROR] Transactional email sending failed: {exc}")
        if db_available:
            try:
                with get_supabase_connection() as connection:
                    with connection.cursor(row_factory=dict_row) as cursor:
                        cursor.execute(
                            """
                            UPDATE public.notifications
                            SET 
                                status = 'FAILED',
                                error_message = %s
                            WHERE notification_id = %s
                            """,
                            (str(exc), notification_id),
                        )
                        connection.commit()
            except Exception:
                pass