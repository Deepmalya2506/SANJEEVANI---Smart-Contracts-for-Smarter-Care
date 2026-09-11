import hashlib
import hmac
import json
from uuid import UUID, uuid4
from typing import Any

# pyrefly: ignore [missing-import]
import razorpay
from fastapi import HTTPException, status
# pyrefly: ignore [missing-import]
from psycopg.rows import dict_row

from app.core.config import settings
from app.core.database import get_supabase_connection, ensure_payments_table_exists


def _client() -> razorpay.Client:
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay test credentials are not configured.",
        )
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_order(data: dict[str, Any]) -> dict[str, Any]:
    """
    Creates a Razorpay order with the proper transaction value in paise.
    Persists the transaction state in Supabase PostgreSQL (public.payments).
    """
    client = _client()
    receipt = data.get("receipt") or f"loan_{uuid4().hex[:24]}"
    
    # Calculate exact transaction value in paise (handling both int and float rupees)
    amount_rupees = float(data["amount_rupees"])
    amount_paise = int(round(amount_rupees * 100))

    if amount_paise <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction amount must be greater than zero.",
        )

    currency = data.get("currency", "INR").upper()
    notes = data.get("notes", {})
    loan_reference = data.get("loan_reference")

    try:
        order = client.order.create({
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "notes": {str(k): str(v) for k, v in notes.items()} if isinstance(notes, dict) else {},
        })
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Razorpay order creation failed: {error}",
        ) from error

    payment_id = uuid4()

    # Persist in Supabase PostgreSQL
    try:
        ensure_payments_table_exists()
        with get_supabase_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.payments (
                        payment_id, order_id, payment_provider_id, loan_reference,
                        amount_paise, amount_rupees, currency, status,
                        receipt, notes, created_at, updated_at
                    )
                    VALUES (%s, %s, NULL, %s, %s, %s, %s, 'PAYMENT_PENDING', %s, %s, now(), now())
                    """,
                    (
                        payment_id,
                        order["id"],
                        loan_reference,
                        amount_paise,
                        amount_rupees,
                        currency,
                        receipt,
                        json.dumps(notes) if notes else None,
                    ),
                )
            connection.commit()
    except Exception as exc:
        print(f"[WARN] Supabase payment logging failed: {exc}")

    return {
        "payment_id": str(payment_id),
        "order_id": order["id"],
        "amount_paise": order["amount"],
        "amount_rupees": amount_rupees,
        "currency": order["currency"],
        "key_id": settings.RAZORPAY_KEY_ID,
        "status": "PAYMENT_PENDING",
        "receipt": receipt,
    }


def verify_payment(data: dict[str, Any]) -> dict[str, Any]:
    """
    Verifies the cryptographic payment signature from Razorpay checkout.
    Updates payment record in Supabase PostgreSQL to PAYMENT_AUTHORIZED.
    """
    client = _client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        })
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Razorpay payment signature verification failed: {error}",
        ) from error

    # Update payment state in Supabase PostgreSQL
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    UPDATE public.payments
                    SET 
                        payment_provider_id = %s,
                        signature = %s,
                        status = 'PAYMENT_AUTHORIZED',
                        updated_at = now()
                    WHERE order_id = %s
                    RETURNING payment_id, loan_reference, amount_rupees
                    """,
                    (
                        data["razorpay_payment_id"],
                        data["razorpay_signature"],
                        data["razorpay_order_id"],
                    ),
                )
                updated_record = cursor.fetchone()

                # Audit activity event
                if updated_record:
                    cursor.execute(
                        """
                        INSERT INTO public.activity_events (
                            activity_id, hospital_id, user_id, entity_type, entity_id, event_type, metadata
                        )
                        VALUES (%s, NULL, NULL, 'PAYMENT', %s, 'payment.authorized', %s)
                        """,
                        (
                            uuid4(),
                            updated_record["payment_id"],
                            json.dumps({
                                "order_id": data["razorpay_order_id"],
                                "payment_id": data["razorpay_payment_id"],
                                "amount_rupees": float(updated_record["amount_rupees"]) if updated_record["amount_rupees"] else None,
                            }),
                        ),
                    )

                    # Update associated loan to ACTIVE if loan_reference exists
                    loan_ref = updated_record.get("loan_reference")
                    if loan_ref:
                        cursor.execute(
                            """
                            UPDATE public.loans
                            SET loan_status = 'ACTIVE', updated_at = now()
                            WHERE loan_id::text = %s OR ('loan-' || SUBSTRING(loan_id::text, 1, 12)) = %s
                            RETURNING loan_id, asset_id, borrower_hospital_id, lender_hospital_id
                            """,
                            (loan_ref, loan_ref),
                        )
                        loan_row = cursor.fetchone()
                        if loan_row:
                            # Update equipment asset to ON_LOAN
                            cursor.execute(
                                """
                                UPDATE public.equipment_assets
                                SET availability_status = 'ON_LOAN', updated_at = now()
                                WHERE asset_id = %s
                                """,
                                (loan_row["asset_id"],),
                            )

                            # Query borrower email
                            cursor.execute(
                                """
                                SELECT u.user_mail, u.admin_name, h.hospital_name
                                FROM public.users u
                                JOIN public.hospitals h ON u.hospital_id = h.hospital_id
                                WHERE u.hospital_id = %s
                                LIMIT 1
                                """,
                                (loan_row["borrower_hospital_id"],),
                            )
                            user_contact = cursor.fetchone()
                            if user_contact and user_contact.get("user_mail"):
                                try:
                                    from app.services.email_services import send_transactional_notification
                                    send_transactional_notification(
                                        hospital_id=loan_row["borrower_hospital_id"],
                                        recipient_email=user_contact["user_mail"],
                                        event_type="PAYMENT_CONFIRMED",
                                        subject="SANJEEVANI — Payment Confirmed & Loan Active",
                                        html_content=f"""
                                        <h2>SANJEEVANI — Payment Confirmed</h2>
                                        <p>Dear {user_contact.get('admin_name', 'Administrator')},</p>
                                        <p>Payment of ₹{float(updated_record['amount_rupees']):,.2f} for loan <strong>{loan_ref}</strong> has been authorized.</p>
                                        <p>Status is now <strong>ACTIVE</strong> and equipment dispatch is authorized.</p>
                                        """,
                                        loan_id=loan_row["loan_id"],
                                    )
                                except Exception as e_err:
                                    print(f"[WARN] Failed to trigger payment confirmed email: {e_err}")
            connection.commit()
    except Exception as exc:
        print(f"[WARN] Supabase payment authorization update failed: {exc}")

    return {
        "status": "PAYMENT_AUTHORIZED",
        "payment_id": data["razorpay_payment_id"],
        "order_id": data["razorpay_order_id"],
    }


def verify_webhook(body: bytes, signature: str) -> bool:
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay webhook secret is not configured.",
        )
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def apply_webhook(event: dict[str, Any]) -> dict[str, Any]:
    """
    Applies an incoming Razorpay webhook event and synchronizes status in Supabase.
    """
    payload = event.get("payload", {})
    payment = payload.get("payment", {}).get("entity", {})
    order_id = payment.get("order_id")

    if not order_id:
        return {"status": "ignored", "reason": "No order_id in webhook payload"}

    event_name = event.get("event", "")
    new_status = {
        "payment.captured": "PAYMENT_CAPTURED",
        "order.paid": "PAYMENT_CAPTURED",
        "payment.failed": "PAYMENT_FAILED",
        "refund.processed": "REFUNDED",
    }.get(event_name)

    if new_status:
        try:
            with get_supabase_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE public.payments
                        SET 
                            status = %s,
                            payment_provider_id = COALESCE(%s, payment_provider_id),
                            updated_at = now()
                        WHERE order_id = %s
                        """,
                        (new_status, payment.get("id"), order_id),
                    )
                connection.commit()
        except Exception as exc:
            print(f"[WARN] Supabase webhook synchronization failed: {exc}")

    return {"status": new_status or "ignored", "order_id": order_id}


def get_payment(identifier: str) -> dict[str, Any] | None:
    """Retrieves payment details by order_id or payment_id from Supabase."""
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT 
                    payment_id, order_id, payment_provider_id, loan_reference,
                    amount_paise, amount_rupees, currency, status,
                    receipt, created_at, updated_at
                FROM public.payments
                WHERE order_id = %s OR payment_id::text = %s
                LIMIT 1
                """,
                (identifier, identifier),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "payment_id": str(row["payment_id"]),
                    "order_id": row["order_id"],
                    "payment_provider_id": row["payment_provider_id"],
                    "loan_reference": row["loan_reference"],
                    "amount_paise": row["amount_paise"],
                    "amount_rupees": float(row["amount_rupees"]) if row["amount_rupees"] is not None else None,
                    "currency": row["currency"],
                    "status": row["status"],
                    "receipt": row["receipt"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                }
            return None