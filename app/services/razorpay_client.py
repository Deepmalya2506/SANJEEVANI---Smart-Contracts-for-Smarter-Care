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
                raw_loan_id = notes.get("loan_id") if isinstance(notes, dict) else None
                try:
                    parsed_loan_id = UUID(raw_loan_id) if raw_loan_id else None
                except Exception:
                    parsed_loan_id = None

                cursor.execute(
                    """
                    INSERT INTO public.payments (
                        payment_id, loan_id, order_id, provider_order_id,
                        payment_provider_id, loan_reference, amount_paise,
                        amount_rupees, charge_amount, currency, provider,
                        purpose, status, receipt, notes, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, NULL, %s, %s, %s, %s, %s, 'RAZORPAY', 'EQUIPMENT_LOAN', 'PAYMENT_PENDING', %s, %s, now(), now())
                    """,
                    (
                        payment_id,
                        parsed_loan_id,
                        order["id"],
                        order["id"],
                        loan_reference,
                        amount_paise,
                        amount_rupees,
                        amount_rupees,
                        currency,
                        receipt,
                        json.dumps(notes) if notes else None,
                    ),
                )
            connection.commit()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Payment order was created but could not be persisted in Supabase: {exc}",
        ) from exc

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
                        provider_payment_id = %s,
                        signature = %s,
                        signature_verified = true,
                        status = 'PAYMENT_AUTHORIZED',
                        updated_at = now()
                    WHERE order_id = %s OR provider_order_id = %s
                    RETURNING payment_id, loan_id, loan_reference, amount_rupees
                    """,
                    (
                        data["razorpay_payment_id"],
                        data["razorpay_payment_id"],
                        data["razorpay_signature"],
                        data["razorpay_order_id"],
                        data["razorpay_order_id"],
                    ),
                )
                updated_record = cursor.fetchone()

                if updated_record is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Razorpay order was not found in Supabase.",
                    )

                # Update associated loan to ACTIVE if loan_reference exists
                loan_ref = updated_record.get("loan_reference")
                loan_id_val = updated_record.get("loan_id")
                loan_row = None
                if loan_ref or loan_id_val:
                    query_clause = "loan_id = %s" if loan_id_val else "(loan_id::text = %s OR ('loan-' || SUBSTRING(loan_id::text, 1, 12)) = %s)"
                    params = (loan_id_val,) if loan_id_val else (loan_ref, loan_ref)
                    cursor.execute(
                        f"""
                        UPDATE public.loans
                        SET loan_status = 'ACTIVE', updated_at = now()
                        WHERE {query_clause}
                        RETURNING loan_id, asset_id, borrower_hospital_id, lender_hospital_id
                        """,
                        params,
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

                # Resolve fallback hospital and user for activity audit
                h_id = loan_row["borrower_hospital_id"] if loan_row else None
                u_id = None
                if not h_id:
                    cursor.execute("SELECT hospital_id FROM public.hospitals LIMIT 1")
                    h_fallback = cursor.fetchone()
                    if h_fallback:
                        h_id = h_fallback["hospital_id"]
                if h_id:
                    cursor.execute("SELECT user_id FROM public.users WHERE hospital_id = %s LIMIT 1", (h_id,))
                    u_row = cursor.fetchone()
                    if u_row:
                        u_id = u_row["user_id"]
                    else:
                        cursor.execute("SELECT user_id FROM public.users LIMIT 1")
                        u_fallback = cursor.fetchone()
                        if u_fallback:
                            u_id = u_fallback["user_id"]

                # Audit activity event
                if h_id and u_id:
                    cursor.execute(
                        """
                        INSERT INTO public.activity_events (
                            activity_id, hospital_id, user_id, entity_type, entity_id, event_type, metadata
                        )
                        VALUES (%s, %s, %s, 'PAYMENT', %s, 'payment.authorized', %s)
                        """,
                        (
                            uuid4(),
                            h_id,
                            u_id,
                            updated_record["payment_id"],
                            json.dumps({
                                "order_id": data["razorpay_order_id"],
                                "payment_id": data["razorpay_payment_id"],
                                "amount_rupees": float(updated_record["amount_rupees"]) if updated_record["amount_rupees"] else None,
                            }),
                        ),
                    )

                # Query borrower email if loan is active
                if loan_row:
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
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Payment verified but Supabase state could not be updated: {exc}",
        ) from exc

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
    Applies an incoming Razorpay webhook event, synchronizes status across payments,
    loans, and equipment_assets in Supabase PostgreSQL, records activity audit events,
    and dispatches transactional email notifications via SMTP.
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
        "payment.authorized": "PAYMENT_AUTHORIZED",
        "payment.failed": "PAYMENT_FAILED",
        "refund.processed": "REFUNDED",
    }.get(event_name)

    if not new_status:
        return {"status": "ignored", "reason": f"Unhandled event '{event_name}'", "order_id": order_id}

    provider_payment_id = payment.get("id")
    amount_rupees_val = payment.get("amount")
    amount_rupees = float(amount_rupees_val) / 100.0 if amount_rupees_val else None

    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                # 1. Check or update public.payments record
                cursor.execute(
                    """
                    SELECT payment_id, loan_id, loan_reference, amount_rupees, currency, provider_payment_id, status
                    FROM public.payments
                    WHERE order_id = %s OR provider_order_id = %s
                    LIMIT 1
                    """,
                    (order_id, order_id),
                )
                existing_payment = cursor.fetchone()
                if not existing_payment:
                    print(f"[WARN] Webhook received for unknown order_id: {order_id}")
                    return {"status": "order_not_found", "order_id": order_id}

                # Update status and provider_payment_id (if not already matching)
                cursor.execute(
                    """
                    UPDATE public.payments
                    SET 
                        status = %s,
                        payment_provider_id = COALESCE(payment_provider_id, %s),
                        provider_payment_id = COALESCE(provider_payment_id, %s),
                        updated_at = now()
                    WHERE payment_id = %s
                    RETURNING payment_id, loan_id, loan_reference, amount_rupees, currency
                    """,
                    (new_status, provider_payment_id, provider_payment_id, existing_payment["payment_id"]),
                )
                payment_record = cursor.fetchone() or existing_payment

                if amount_rupees is None and payment_record.get("amount_rupees"):
                    amount_rupees = float(payment_record["amount_rupees"])

                loan_ref = payment_record.get("loan_reference")
                loan_id_val = payment_record.get("loan_id")

                # 2. Synchronize loan and equipment status based on webhook payment state
                loan_row = None
                if loan_ref or loan_id_val:
                    query_clause = "loan_id = %s" if loan_id_val else "(loan_id::text = %s OR ('loan-' || SUBSTRING(loan_id::text, 1, 12)) = %s)"
                    params = (loan_id_val,) if loan_id_val else (loan_ref, loan_ref)

                    if new_status in ("PAYMENT_CAPTURED", "PAYMENT_AUTHORIZED"):
                        cursor.execute(
                            f"""
                            UPDATE public.loans
                            SET loan_status = 'ACTIVE', updated_at = now()
                            WHERE {query_clause}
                            RETURNING loan_id, asset_id, borrower_hospital_id, lender_hospital_id, duration_hours
                            """,
                            params,
                        )
                        loan_row = cursor.fetchone()
                        if loan_row:
                            cursor.execute(
                                """
                                UPDATE public.equipment_assets
                                SET availability_status = 'ON_LOAN', updated_at = now()
                                WHERE asset_id = %s
                                """,
                                (loan_row["asset_id"],),
                            )
                            # Record state transition
                            cursor.execute(
                                """
                                INSERT INTO public.loan_state_events (
                                    event_id, loan_id, previous_state, new_state, actor_type, actor_id, source
                                )
                                VALUES (%s, %s, 'APPROVED', 'ACTIVE', 'GATEWAY', %s, 'razorpay.webhook')
                                """,
                                (uuid4(), loan_row["loan_id"], loan_row["borrower_hospital_id"]),
                            )

                    elif new_status == "PAYMENT_FAILED":
                        cursor.execute(
                            f"""
                            UPDATE public.loans
                            SET loan_status = 'PAYMENT_FAILED', updated_at = now()
                            WHERE {query_clause}
                            RETURNING loan_id, asset_id, borrower_hospital_id, lender_hospital_id
                            """,
                            params,
                        )
                        loan_row = cursor.fetchone()
                        if loan_row:
                            # Release equipment reservation back to AVAILABLE
                            cursor.execute(
                                """
                                UPDATE public.equipment_assets
                                SET availability_status = 'AVAILABLE', updated_at = now()
                                WHERE asset_id = %s
                                """,
                                (loan_row["asset_id"],),
                            )

                # 3. Resolve hospital and user identities for audit event
                act_hospital_id = loan_row["borrower_hospital_id"] if loan_row else None
                act_user_id = None
                
                # Verify that act_hospital_id actually exists in public.hospitals
                if act_hospital_id:
                    cursor.execute("SELECT hospital_id FROM public.hospitals WHERE hospital_id = %s", (act_hospital_id,))
                    if not cursor.fetchone():
                        act_hospital_id = None

                if not act_hospital_id:
                    cursor.execute("SELECT hospital_id FROM public.hospitals LIMIT 1")
                    h_fb = cursor.fetchone()
                    if h_fb:
                        act_hospital_id = h_fb["hospital_id"]

                if act_hospital_id:
                    cursor.execute("SELECT user_id FROM public.users WHERE hospital_id = %s LIMIT 1", (act_hospital_id,))
                    u_fb = cursor.fetchone()
                    if u_fb:
                        act_user_id = u_fb["user_id"]
                    else:
                        cursor.execute("SELECT user_id FROM public.users LIMIT 1")
                        u_fb2 = cursor.fetchone()
                        if u_fb2:
                            act_user_id = u_fb2["user_id"]

                # Record audit activity event
                if act_hospital_id and act_user_id:
                    cursor.execute(
                        """
                        INSERT INTO public.activity_events (
                            activity_id, hospital_id, user_id, entity_type, entity_id, event_type, metadata
                        )
                        VALUES (%s, %s, %s, 'PAYMENT', %s, %s, %s)
                        """,
                        (
                            uuid4(),
                            act_hospital_id,
                            act_user_id,
                            payment_record["payment_id"],
                            event_name,
                            json.dumps({
                                "order_id": order_id,
                                "payment_id": provider_payment_id,
                                "status": new_status,
                                "amount_rupees": amount_rupees,
                                "event": event_name,
                            }),
                        ),
                    )

                # 4. Fetch involved contacts for Email SMTP notifications
                contacts_to_notify = []
                hospital_ids_to_query = []
                if loan_row:
                    if loan_row.get("borrower_hospital_id"):
                        hospital_ids_to_query.append(loan_row["borrower_hospital_id"])
                    if loan_row.get("lender_hospital_id"):
                        hospital_ids_to_query.append(loan_row["lender_hospital_id"])

                if hospital_ids_to_query:
                    cursor.execute(
                        """
                        SELECT u.user_mail, u.admin_name, h.hospital_name, h.hospital_id
                        FROM public.users u
                        JOIN public.hospitals h ON u.hospital_id = h.hospital_id
                        WHERE u.hospital_id = ANY(%s)
                        """,
                        (hospital_ids_to_query,),
                    )
                    contacts_to_notify = cursor.fetchall()

                # Fallback: If no loan contacts were resolved, notify the payer or network admin
                if not contacts_to_notify:
                    payer_email = payment.get("email")
                    cursor.execute(
                        """
                        SELECT u.user_mail, u.admin_name, h.hospital_name, h.hospital_id
                        FROM public.users u
                        JOIN public.hospitals h ON u.hospital_id = h.hospital_id
                        LIMIT 1
                        """
                    )
                    default_admin = cursor.fetchone()
                    if default_admin:
                        contacts_to_notify = [
                            {
                                "user_mail": payer_email or default_admin["user_mail"],
                                "admin_name": default_admin.get("admin_name", "Administrator"),
                                "hospital_name": default_admin.get("hospital_name", "Hospital"),
                                "hospital_id": default_admin.get("hospital_id"),
                            }
                        ]

                connection.commit()

                # 5. Dispatch email SMTP notifications
                from app.services.email_services import send_transactional_notification

                subject_map = {
                    "PAYMENT_CAPTURED": "SANJEEVANI — Payment Captured & Clearance Granted",
                    "PAYMENT_AUTHORIZED": "SANJEEVANI — Payment Authorized & Dispatch Activated",
                    "PAYMENT_FAILED": "SANJEEVANI — Payment Failed & Asset Released",
                    "REFUNDED": "SANJEEVANI — Transaction Refund Processed",
                }
                subject = subject_map.get(new_status, f"SANJEEVANI — Transaction Update: {new_status}")

                for contact in contacts_to_notify:
                    recipient = contact.get("user_mail")
                    if not recipient:
                        continue
                    admin_name = contact.get("admin_name", "Administrator")
                    hosp_name = contact.get("hospital_name", "Hospital")

                    html_content = f"""
                    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;">
                        <h2 style="color: #0f172a; margin-top: 0;">SANJEEVANI Care Network</h2>
                        <p style="font-size: 15px; color: #334155;">Dear {admin_name} ({hosp_name}),</p>
                        <p style="font-size: 14px; color: #334155;">
                            A Razorpay payment transaction update has been received and verified for your care network allocation.
                        </p>
                        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 16px; margin: 16px 0;">
                            <ul style="list-style: none; padding: 0; margin: 0; font-size: 13px; color: #1e293b; line-height: 1.8;">
                                <li><strong>Transaction Event:</strong> <code style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px;">{event_name}</code></li>
                                <li><strong>Payment Status:</strong> <span style="font-weight: 700; color: #0284c7;">{new_status}</span></li>
                                <li><strong>Razorpay Order ID:</strong> {order_id}</li>
                                <li><strong>Razorpay Payment ID:</strong> {provider_payment_id or 'N/A'}</li>
                                <li><strong>Amount:</strong> ₹{amount_rupees:,.2f} INR</li>
                                <li><strong>Loan Reference:</strong> {loan_ref or str(loan_id_val) or 'Direct Escrow'}</li>
                            </ul>
                        </div>
                        <p style="font-size: 13px; color: #64748b;">
                            This confirmation was recorded to the immutable ledger in Supabase PostgreSQL and authenticated via cryptographic HMAC signature.
                        </p>
                        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
                        <p style="font-size: 12px; color: #94a3b8; margin: 0;">
                            SANJEEVANI Emergency Medical Logistics Protocol · Secure Transaction Webhook System
                        </p>
                    </div>
                    """
                    try:
                        send_transactional_notification(
                            hospital_id=contact.get("hospital_id"),
                            recipient_email=recipient,
                            event_type=f"WEBHOOK_{new_status}",
                            subject=subject,
                            html_content=html_content,
                            loan_id=loan_row["loan_id"] if loan_row else None,
                        )
                    except Exception as email_err:
                        print(f"[WARN] Webhook email notification delivery failed for {recipient}: {email_err}")

        print(f"[INFO] Razorpay webhook applied successfully: order_id={order_id} status={new_status}")
    except Exception as exc:
        print(f"[ERROR] Supabase webhook synchronization failed: {exc}")
        return {"status": "error", "message": str(exc), "order_id": order_id}

    return {
        "status": new_status,
        "order_id": order_id,
        "payment_id": provider_payment_id,
        "amount_rupees": amount_rupees,
    }


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