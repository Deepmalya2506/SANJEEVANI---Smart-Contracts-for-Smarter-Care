# send_custom_notification.py
import sys
from uuid import UUID
from psycopg.rows import dict_row

from app.core.database import get_supabase_connection
from app.services.email_services import send_transactional_notification


def send_custom_message(hospital_id_str: str, message_body: str):
    # 1. Validate UUID format
    try:
        hospital_uuid = UUID(hospital_id_str.strip())
    except ValueError:
        print(f"Error: '{hospital_id_str}' is not a valid UUID.")
        return

    # 2. Query target hospital and administrator details
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT 
                    h.hospital_id,
                    h.hospital_name,
                    u.admin_name,
                    u.user_mail
                FROM public.hospitals h
                JOIN public.users u ON h.hospital_id = u.hospital_id
                WHERE h.hospital_id = %s
                LIMIT 1
                """,
                (hospital_uuid,),
            )
            hospital_record = cursor.fetchone()

    if not hospital_record:
        print(f"Error: No hospital or registered administrator found for ID: {hospital_uuid}")
        return

    admin_name = hospital_record["admin_name"]
    recipient_email = hospital_record["user_mail"]
    hospital_name = hospital_record["hospital_name"]

    print(f"Target Found: {hospital_name}")
    print(f"Recipient: {admin_name} <{recipient_email}>")

    # 3. Format email body
    html_content = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>SANJEEVANI System Message</h2>
        <p>Dear <strong>{admin_name}</strong>,</p>
        <p>You have received a direct communication regarding <strong>{hospital_name}</strong>:</p>
        <div style="background-color: #f4f4f5; padding: 15px; border-left: 4px solid #0284c7; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0; white-space: pre-wrap;">{message_body}</p>
        </div>
        <p style="font-size: 12px; color: #666;">This is an automated operational transmission from the SANJEEVANI Network.</p>
    </div>
    """

    # 4. Dispatch email and log to public.notifications
    print("Dispatching via Brevo SMTP relay...")
    send_transactional_notification(
        hospital_id=hospital_uuid,
        recipient_email=recipient_email,
        event_type="CUSTOM_TEST_MESSAGE",
        subject=f"SANJEEVANI Notification — {hospital_name}",
        html_content=html_content,
    )

    # 5. Verify delivery status from database
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT status, sent_at, error_message
                FROM public.notifications
                WHERE hospital_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (hospital_uuid,),
            )
            latest_status = cursor.fetchone()

    if latest_status and latest_status["status"] == "SENT":
        print(f"Success: Message delivered to {recipient_email} at {latest_status['sent_at']}.")
    else:
        err = latest_status["error_message"] if latest_status else "Unknown error"
        print(f"Failure: Delivery status is {latest_status['status'] if latest_status else 'UNKNOWN'}. Details: {err}")


if __name__ == "__main__":
    # Allows passing arguments via CLI or via interactive terminal prompts
    if len(sys.argv) >= 3:
        h_id = sys.argv[1]
        msg = " ".join(sys.argv[2:])
    else:
        h_id = input("Enter hospital_id (UUID): ").strip()
        msg = input("Enter custom message to send: ").strip()

    if h_id and msg:
        send_custom_message(h_id, msg)
    else:
        print("Both hospital_id and message are required.")