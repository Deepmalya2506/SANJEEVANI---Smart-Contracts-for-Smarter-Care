from datetime import datetime, timezone
import io
import json
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, Request, UploadFile, status
import pandas as pd
# pyrefly: ignore [missing-import]
from psycopg.rows import dict_row

from app.core.database import get_supabase_connection
from app.schemas.inventory import (
    EquipmentAssetCreate,
    EquipmentAssetResponse,
    HospitalInventoryGroup,
    SanctionTransactionRequest,
)
from app.services.email_services import send_transactional_notification
from app.services.razorpay_client import create_order

router = APIRouter()


def _resolve_hospital_and_admin(
    cursor,
    explicit_hospital_id: UUID | str | None = None,
    request: Request | None = None,
) -> tuple[UUID, UUID | None, str | None, str | None, str | None]:
    """Resolves (hospital_id, user_id, admin_name, user_mail, mvp_hfr_id)."""
    # 1. Try Bearer token from Request header
    if request:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            if token:
                try:
                    from app.core.dependencies import get_current_user
                    from fastapi.security import HTTPAuthorizationCredentials

                    user_ctx = get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
                    return (
                        user_ctx.hospital_id,
                        user_ctx.user_id,
                        user_ctx.admin_name,
                        user_ctx.user_mail,
                        user_ctx.mvp_hfr_id,
                    )
                except Exception:
                    pass

    # 2. Try explicit hospital_id
    if explicit_hospital_id:
        try:
            h_uuid = UUID(str(explicit_hospital_id).strip())
            cursor.execute(
                """
                SELECT h.hospital_id, h.mvp_hfr_id, u.user_id, u.admin_name, u.user_mail
                FROM public.hospitals h
                LEFT JOIN public.users u ON h.hospital_id = u.hospital_id
                WHERE h.hospital_id = %s
                LIMIT 1
                """,
                (h_uuid,),
            )
            row = cursor.fetchone()
            if row:
                return (
                    row["hospital_id"],
                    row.get("user_id"),
                    row.get("admin_name"),
                    row.get("user_mail"),
                    row.get("mvp_hfr_id"),
                )
        except Exception:
            pass

    # 3. Fallback to first active hospital in database
    cursor.execute(
        """
        SELECT h.hospital_id, h.mvp_hfr_id, u.user_id, u.admin_name, u.user_mail
        FROM public.hospitals h
        LEFT JOIN public.users u ON h.hospital_id = u.hospital_id
        ORDER BY h.created_at ASC
        LIMIT 1
        """
    )
    fallback = cursor.fetchone()
    if fallback:
        return (
            fallback["hospital_id"],
            fallback.get("user_id"),
            fallback.get("admin_name"),
            fallback.get("user_mail"),
            fallback.get("mvp_hfr_id"),
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No registered hospital organization found. Please complete hospital signup first.",
    )


@router.post(
    "/api/v1/equipment/assets",
    response_model=EquipmentAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/equipment/assets",
    response_model=EquipmentAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/equipment/register",
    response_model=EquipmentAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_equipment_asset(
    data: EquipmentAssetCreate,
    request: Request,
    background_tasks: BackgroundTasks,
):
    asset_id = uuid4()
    hospital_id = getattr(data, "hospital_id", None) or uuid4()
    user_id = uuid4()
    admin_name = "Administrator"
    user_mail = None

    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                resolved_hid, resolved_uid, resolved_aname, resolved_umail, mvp_hfr_id = _resolve_hospital_and_admin(
                    cursor, data.hospital_id, request
                )
                if resolved_hid:
                    hospital_id = resolved_hid
                if resolved_uid:
                    user_id = resolved_uid
                if resolved_aname:
                    admin_name = resolved_aname
                if resolved_umail:
                    user_mail = resolved_umail

                lat = data.latitude
                lon = data.longitude

                # Fallback to ABDM directory coordinates if asset location is not provided
                if (lat is None or lon is None) and mvp_hfr_id:
                    cursor.execute(
                        """
                        SELECT latitude, longitude 
                        FROM public.abdm_mock_hfr 
                        WHERE mvp_hfr_id = %s
                        """,
                        (mvp_hfr_id,),
                    )
                    hfr_record = cursor.fetchone()
                    if hfr_record and hfr_record["latitude"] is not None and hfr_record["longitude"] is not None:
                        lat = float(hfr_record["latitude"])
                        lon = float(hfr_record["longitude"])

                cursor.execute(
                    """
                    INSERT INTO public.equipment_assets (
                        asset_id, hospital_id, equipment_type, name, serial_number,
                        condition_status, availability_status, shareable,
                        location, hourly_rate, metadata
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, 'AVAILABLE', %s,
                        CASE 
                            WHEN %s::float8 IS NOT NULL AND %s::float8 IS NOT NULL 
                            THEN ST_SetSRID(ST_MakePoint(%s::float8, %s::float8), 4326)
                            ELSE NULL 
                        END,
                        %s, %s
                    )
                    RETURNING 
                        asset_id, hospital_id, equipment_type, name, serial_number,
                        condition_status, availability_status, shareable, hourly_rate,
                        ST_Y(location) AS latitude, ST_X(location) AS longitude, created_at
                    """,
                    (
                        asset_id,
                        hospital_id,
                        data.equipment_type.strip(),
                        data.name.strip(),
                        data.serial_number.strip() if data.serial_number else None,
                        data.condition_status.strip().upper(),
                        data.shareable,
                        lon,
                        lat,
                        lon,
                        lat,
                        data.hourly_rate,
                        json.dumps(data.metadata) if data.metadata else None,
                    ),
                )
                created_asset = cursor.fetchone()

                cursor.execute(
                    """
                    INSERT INTO public.activity_events (
                        activity_id, hospital_id, user_id, entity_type, entity_id, event_type, metadata
                    )
                    VALUES (%s, %s, %s, 'ASSET', %s, 'asset.created', %s)
                    """,
                    (
                        uuid4(),
                        hospital_id,
                        user_id,
                        asset_id,
                        json.dumps({
                            "name": data.name,
                            "equipment_type": data.equipment_type,
                        }),
                    ),
                )
                connection.commit()

                # Enqueue transactional email confirmation if admin email is resolved
                if user_mail:
                    email_body = f"""
                    <h2>SANJEEVANI — Equipment Registered</h2>
                    <p>Dear {admin_name or 'Administrator'},</p>
                    <p>Your equipment asset <strong>{data.name}</strong> ({data.equipment_type}) is now registered in the SANJEEVANI network inventory.</p>
                    <ul>
                        <li><strong>Asset ID:</strong> {asset_id}</li>
                        <li><strong>Status:</strong> AVAILABLE</li>
                        <li><strong>Condition:</strong> {data.condition_status.upper()}</li>
                        <li><strong>Hourly Rate:</strong> ₹{data.hourly_rate:,.2f}</li>
                    </ul>
                    """
                    background_tasks.add_task(
                        send_transactional_notification,
                        hospital_id=hospital_id,
                        recipient_email=user_mail,
                        event_type="EQUIPMENT_REGISTERED",
                        subject=f"SANJEEVANI — Equipment Registered: {data.name}",
                        html_content=email_body,
                    )

        if created_asset is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register equipment asset.",
            )

        return created_asset
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unavailable: {exc}",
        ) from exc


@router.post("/inventory/upload", status_code=status.HTTP_201_CREATED)
@router.post("/api/v1/inventory/upload", status_code=status.HTTP_201_CREATED)
async def upload_inventory_csv(
    file: UploadFile = File(...),
    request: Request = None,
    background_tasks: BackgroundTasks = None,
):
    if not (file.filename or "").endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid CSV file.",
        )

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to parse CSV file: {exc}",
        ) from exc

    required_columns = {"name", "equipment_type"}
    if not required_columns.issubset(df.columns):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV missing mandatory columns: {required_columns - set(df.columns)}",
        )

    records = df.to_dict(orient="records")
    inserted_count = 0

    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                hospital_id, user_id, admin_name, user_mail, mvp_hfr_id = _resolve_hospital_and_admin(
                    cursor, None, request
                )

                # Fallback coordinates from hospital registry record
                default_lat = None
                default_lon = None
                if mvp_hfr_id:
                    cursor.execute(
                        """
                        SELECT latitude, longitude 
                        FROM public.abdm_mock_hfr 
                        WHERE mvp_hfr_id = %s
                        """,
                        (mvp_hfr_id,),
                    )
                    hfr_row = cursor.fetchone()
                    if hfr_row and hfr_row["latitude"] is not None:
                        default_lat = float(hfr_row["latitude"])
                        default_lon = float(hfr_row["longitude"])

                for row in records:
                    asset_id = uuid4()
                    lat = float(row["latitude"]) if pd.notna(row.get("latitude")) else default_lat
                    lon = float(row["longitude"]) if pd.notna(row.get("longitude")) else default_lon
                    rate = float(row.get("hourly_rate", 0.0)) if pd.notna(row.get("hourly_rate")) else 0.0
                    serial = str(row["serial_number"]).strip() if pd.notna(row.get("serial_number")) else None
                    condition = str(row.get("condition_status", "OPERATIONAL")).strip().upper()
                    shareable = bool(row.get("shareable", True))

                    cursor.execute(
                        """
                        INSERT INTO public.equipment_assets (
                            asset_id, hospital_id, equipment_type, name, serial_number,
                            condition_status, availability_status, shareable,
                            location, hourly_rate, metadata
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            %s, 'AVAILABLE', %s,
                            CASE 
                            WHEN %s::float8 IS NOT NULL AND %s::float8 IS NOT NULL 
                            THEN ST_SetSRID(ST_MakePoint(%s::float8, %s::float8), 4326)
                            ELSE NULL 
                        END,
                            %s, %s
                        )
                        """,
                        (
                            asset_id,
                            hospital_id,
                            str(row["equipment_type"]).strip(),
                            str(row["name"]).strip(),
                            serial,
                            condition,
                            shareable,
                            lon,
                            lat,
                            lon,
                            lat,
                            rate,
                            json.dumps({"source": "csv_bulk_import"}),
                        ),
                    )
                    inserted_count += 1

                connection.commit()

                # Optional email notification for bulk import
                if background_tasks and user_mail:
                    email_body = f"""
                    <h2>SANJEEVANI — Bulk Inventory Import Complete</h2>
                    <p>Dear {admin_name or 'Administrator'},</p>
                    <p>Successfully imported <strong>{inserted_count}</strong> equipment assets from <code>{file.filename}</code> into your active inventory.</p>
                    """
                    background_tasks.add_task(
                        send_transactional_notification,
                        hospital_id=hospital_id,
                        recipient_email=user_mail,
                        event_type="EQUIPMENT_BATCH_REGISTERED",
                        subject=f"SANJEEVANI — {inserted_count} Equipment Assets Ingested",
                        html_content=email_body,
                    )

        return {
            "status": "success",
            "message": f"Successfully ingested {inserted_count} equipment assets into your inventory.",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unreachable: {exc}. Please verify SUPABASE_HOST and credentials in .env.",
        ) from exc


# ============================================================================
# Transaction Sanctioning (Equipment Loan Approval & Razorpay Order Setup)
# ============================================================================
@router.post("/api/v1/transactions/sanction")
@router.post("/transactions/sanction")
def sanction_equipment_transaction(
    data: SanctionTransactionRequest,
    request: Request = None,
    background_tasks: BackgroundTasks = None,
):
    """
    Sanctions an equipment loan between borrowing and lending hospitals.
    1. Locks the equipment asset (status -> 'RESERVED').
    2. Registers the approved loan record in public.loans.
    3. Formulates the exact Razorpay payment order in paise (rupees * 100).
    4. Triggers transactional notifications to involved administrators.
    """
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                # 1. Resolve borrower hospital
                borrower_hospital_id = None
                if data.borrower_hospital_id:
                    try:
                        borrower_hospital_id = UUID(str(data.borrower_hospital_id).strip())
                    except Exception:
                        pass

                if not borrower_hospital_id:
                    b_hid, _, _, _, _ = _resolve_hospital_and_admin(cursor, None, request)
                    borrower_hospital_id = b_hid

                # 2. Resolve lender hospital
                try:
                    lender_hospital_id = UUID(str(data.lender_hospital_id).strip())
                except Exception as exc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid lender_hospital_id format: {exc}",
                    )

                if borrower_hospital_id and lender_hospital_id == borrower_hospital_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Lender hospital and borrower hospital must be distinct organizations. A hospital cannot sanction an inter-hospital equipment loan to itself.",
                    )

                # 3. Locate or resolve matching equipment asset
                asset_record = None
                if data.asset_id:
                    try:
                        target_asset_uuid = UUID(str(data.asset_id).strip())
                        cursor.execute(
                            """
                            SELECT asset_id, hospital_id, equipment_type, name, hourly_rate, availability_status
                            FROM public.equipment_assets
                            WHERE asset_id = %s AND hospital_id = %s
                            """,
                            (target_asset_uuid, lender_hospital_id),
                        )
                        asset_record = cursor.fetchone()
                    except Exception:
                        pass

                if not asset_record:
                    # Find first available asset of the requested type at the lender hospital
                    cursor.execute(
                        """
                        SELECT asset_id, hospital_id, equipment_type, name, hourly_rate, availability_status
                        FROM public.equipment_assets
                        WHERE hospital_id = %s
                          AND LOWER(equipment_type) = LOWER(%s)
                          AND availability_status = 'AVAILABLE'
                        LIMIT 1
                        """,
                        (lender_hospital_id, data.equipment_type.strip()),
                    )
                    asset_record = cursor.fetchone()

                if not asset_record:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No available matching equipment asset exists in Supabase.",
                    )

                resolved_asset_id = asset_record["asset_id"]
                cursor.execute(
                    """
                    UPDATE public.equipment_assets
                    SET availability_status = 'RESERVED', updated_at = now()
                    WHERE asset_id = %s AND availability_status = 'AVAILABLE'
                    """,
                    (resolved_asset_id,),
                )
                if cursor.rowcount != 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="The selected equipment asset is no longer available.",
                    )

                # 5. Create reservation and sanction loan entry
                reservation_id = uuid4()
                try:
                    cursor.execute(
                        """
                        INSERT INTO public.reservations (
                            reservation_id, asset_id, borrower_hospital_id, starts_at, ends_at, hold_expires_at, status, idempotency_key
                        )
                        VALUES (%s, %s, %s, now(), now() + interval '%s hours', now() + interval '2 hours', 'CONFIRMED', %s)
                        """,
                        (reservation_id, resolved_asset_id, borrower_hospital_id, data.duration_hours, uuid4().hex),
                    )
                except Exception as res_err:
                    print(f"[WARN] Reservation insert fallback: {res_err}")
                    reservation_id = None

                loan_id = uuid4()
                cursor.execute(
                    """
                    INSERT INTO public.loans (
                        loan_id, reservation_id, asset_id, lender_hospital_id, borrower_hospital_id,
                        loan_status, amount, duration_hours, notes
                    )
                    VALUES (%s, %s, %s, %s, %s, 'APPROVED', %s, %s, %s)
                    """,
                    (
                        loan_id,
                        reservation_id,
                        resolved_asset_id,
                        lender_hospital_id,
                        borrower_hospital_id,
                        data.amount_rupees,
                        data.duration_hours,
                        json.dumps(data.notes if isinstance(data.notes, dict) else {"notes": str(data.notes)}),
                    ),
                )

                # 6. Audit state transition
                cursor.execute(
                    """
                    INSERT INTO public.loan_state_events (
                        event_id, loan_id, previous_state, new_state, actor_type, actor_id, source
                    )
                    VALUES (%s, %s, 'REQUESTED', 'APPROVED', 'ADMIN', %s, 'api.transactions.sanction')
                    """,
                    (uuid4(), loan_id, borrower_hospital_id),
                )
                connection.commit()

                # 7. Create Razorpay Payment Order with exact conversion (Rupees -> Paise)
                amount_paise = int(round(float(data.amount_rupees) * 100))
                order = create_order({
                    "amount_rupees": data.amount_rupees,
                    "currency": "INR",
                    "loan_reference": f"loan-{loan_id.hex[:12]}",
                    "receipt": f"rcpt_{loan_id.hex[:16]}",
                    "notes": {
                        "loan_id": str(loan_id),
                        "asset_id": str(resolved_asset_id),
                        "equipment_type": data.equipment_type,
                        "lender_hospital_id": str(lender_hospital_id),
                        "borrower_hospital_id": str(borrower_hospital_id),
                    },
                })

                # 8. Query borrower and lender emails for notifications
                cursor.execute(
                    """
                    SELECT u.user_mail, u.admin_name, h.hospital_name
                    FROM public.users u
                    JOIN public.hospitals h ON u.hospital_id = h.hospital_id
                    WHERE u.hospital_id IN (%s, %s)
                    """,
                    (borrower_hospital_id, lender_hospital_id),
                )
                admin_contacts = cursor.fetchall()
                connection.commit()

                # 9. Dispatch transactional notifications
                recipients = []
                for contact in admin_contacts:
                    if contact.get("user_mail"):
                        recipients.append({
                            "email": contact["user_mail"],
                            "name": contact.get("admin_name", "Administrator"),
                        })

                if data.borrower_admin_email and not any(r["email"].lower() == data.borrower_admin_email.strip().lower() for r in recipients):
                    recipients.append({
                        "email": data.borrower_admin_email.strip(),
                        "name": "Borrower Administrator",
                    })

                for recipient in recipients:
                    sanction_email = f"""
                    <h2>SANJEEVANI — Equipment Transaction Sanctioned</h2>
                    <p>Dear {recipient['name']},</p>
                    <p>The equipment loan transaction for <strong>{data.equipment_type}</strong> has been successfully sanctioned.</p>
                    <ul>
                        <li><strong>Loan ID:</strong> {loan_id}</li>
                        <li><strong>Transaction Amount:</strong> ₹{data.amount_rupees:,.2f} ({amount_paise} paise)</li>
                        <li><strong>Razorpay Order ID:</strong> {order.get('order_id')}</li>
                        <li><strong>Duration:</strong> {data.duration_hours} Hours</li>
                        <li><strong>Asset Status:</strong> RESERVED</li>
                    </ul>
                    <p>Dispatch clearance is granted upon payment authorization.</p>
                    """
                    if background_tasks:
                        background_tasks.add_task(
                            send_transactional_notification,
                            hospital_id=borrower_hospital_id,
                            recipient_email=recipient["email"],
                            event_type="TRANSACTION_SANCTIONED",
                            subject=f"SANJEEVANI — Transaction Sanctioned: {data.equipment_type}",
                            html_content=sanction_email,
                            loan_id=loan_id,
                        )
                    else:
                        try:
                            send_transactional_notification(
                                hospital_id=borrower_hospital_id,
                                recipient_email=recipient["email"],
                                event_type="TRANSACTION_SANCTIONED",
                                subject=f"SANJEEVANI — Transaction Sanctioned: {data.equipment_type}",
                                html_content=sanction_email,
                                loan_id=loan_id,
                            )
                        except Exception as notif_err:
                            print(f"[WARN] Direct notification dispatch error: {notif_err}")

                return {
                    "status": "SANCTIONED",
                    "loan_id": str(loan_id),
                    "order_id": order.get("order_id"),
                    "amount_rupees": data.amount_rupees,
                    "amount_paise": amount_paise,
                    "equipment_type": data.equipment_type,
                    "asset_id": str(resolved_asset_id),
                    "lender_hospital_id": str(lender_hospital_id),
                    "borrower_hospital_id": str(borrower_hospital_id),
                    "loan_status": "APPROVED",
                    "asset_status": "RESERVED",
                    "payment_order": order,
                    "message": "Equipment loan transaction sanctioned successfully. Razorpay checkout order generated.",
                }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase transaction unavailable: {exc}",
        ) from exc



EQUIPMENT_NUMERIC_MAP = {
    "1": "Oxygen concentrator",
    "2": "Portable ventilator",
    "3": "Patient monitor",
    "4": "Infusion pump",
}

@router.get("/inventory/search")
@router.get("/api/v1/inventory/search")
def search_inventory(
    equipment_type: str | None = Query(default=None),
    quantity: int = Query(default=1, gt=0),
):
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                if equipment_type and equipment_type.strip():
                    clean_type = equipment_type.strip()
                    resolved_type = EQUIPMENT_NUMERIC_MAP.get(clean_type, clean_type)
                    cursor.execute(
                        """
                        SELECT 
                            ea.hospital_id,
                            h.hospital_name,
                            ea.equipment_type,
                            COUNT(ea.asset_id)::int AS available_count,
                            AVG(ST_Y(ea.location))::float8 AS latitude,
                            AVG(ST_X(ea.location))::float8 AS longitude
                        FROM public.equipment_assets ea
                        JOIN public.hospitals h ON ea.hospital_id = h.hospital_id
                        WHERE (LOWER(ea.equipment_type) = LOWER(%s) OR LOWER(ea.equipment_type) = LOWER(%s))
                          AND ea.availability_status = 'AVAILABLE'
                          AND ea.shareable = true
                        GROUP BY ea.hospital_id, h.hospital_name, ea.equipment_type
                        HAVING COUNT(ea.asset_id) >= %s
                        ORDER BY available_count DESC
                        """,
                        (clean_type, resolved_type, quantity),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT 
                            ea.hospital_id,
                            h.hospital_name,
                            ea.equipment_type,
                            COUNT(ea.asset_id)::int AS available_count,
                            AVG(ST_Y(ea.location))::float8 AS latitude,
                            AVG(ST_X(ea.location))::float8 AS longitude
                        FROM public.equipment_assets ea
                        JOIN public.hospitals h ON ea.hospital_id = h.hospital_id
                        WHERE ea.availability_status = 'AVAILABLE'
                          AND ea.shareable = true
                        GROUP BY ea.hospital_id, h.hospital_name, ea.equipment_type
                        HAVING COUNT(ea.asset_id) >= %s
                        ORDER BY available_count DESC
                        """,
                        (quantity,),
                    )
                return cursor.fetchall()
    except Exception as exc:
        print(f"[WARN] Supabase inventory search error: {exc}")
        return []


@router.get("/equipment/assets")
@router.get("/api/v1/equipment/assets")
def list_all_equipment_assets(
    hospital_id: str | None = None,
    availability_status: str | None = None,
    limit: int = 50,
):
    """Returns all registered equipment assets with hospital details directly from Supabase."""
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                query = """
                SELECT 
                    ea.asset_id, ea.hospital_id, ea.equipment_type, ea.name,
                    ea.serial_number, ea.condition_status, ea.availability_status,
                    ea.shareable, ea.hourly_rate, ea.metadata, ea.created_at,
                    h.hospital_name, h.mvp_hfr_id
                FROM public.equipment_assets ea
                LEFT JOIN public.hospitals h ON ea.hospital_id = h.hospital_id
                WHERE 1=1
                """
                params = []
                if hospital_id:
                    query += " AND ea.hospital_id = %s"
                    params.append(hospital_id)
                if availability_status:
                    query += " AND ea.availability_status = %s"
                    params.append(availability_status)
                query += " ORDER BY ea.created_at DESC LIMIT %s"
                params.append(limit)
                cursor.execute(query, tuple(params))
                return cursor.fetchall()
    except Exception as exc:
        print(f"[WARN] Supabase equipment assets query failed: {exc}")
        return []


@router.get("/loans")
@router.get("/api/v1/loans")
def list_loans(hospital_id: str | None = None, limit: int = 50):
    """Returns real equipment loans from Supabase."""
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                query = """
                SELECT 
                    l.loan_id, l.reservation_id, l.asset_id, l.borrower_hospital_id,
                    l.lender_hospital_id, l.loan_status, l.amount, l.duration_hours,
                    l.notes, l.created_at, l.updated_at,
                    bh.hospital_name AS borrower_hospital_name,
                    lh.hospital_name AS lender_hospital_name,
                    ea.name AS asset_name, ea.equipment_type
                FROM public.loans l
                LEFT JOIN public.hospitals bh ON l.borrower_hospital_id = bh.hospital_id
                LEFT JOIN public.hospitals lh ON l.lender_hospital_id = lh.hospital_id
                LEFT JOIN public.equipment_assets ea ON l.asset_id = ea.asset_id
                WHERE 1=1
                """
                params = []
                if hospital_id:
                    query += " AND (l.borrower_hospital_id = %s OR l.lender_hospital_id = %s)"
                    params.extend([hospital_id, hospital_id])
                query += " ORDER BY l.created_at DESC LIMIT %s"
                params.append(limit)
                cursor.execute(query, tuple(params))
                return cursor.fetchall()
    except Exception as exc:
        print(f"[WARN] Supabase loans query failed: {exc}")
        return []


@router.get("/inventory/{hospital_id}", response_model=list[EquipmentAssetResponse])
@router.get("/api/v1/inventory/{hospital_id}", response_model=list[EquipmentAssetResponse])
def get_hospital_inventory(hospital_id: str):
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        asset_id, hospital_id, equipment_type, name, serial_number,
                        condition_status, availability_status, shareable, hourly_rate,
                        ST_Y(location) AS latitude, ST_X(location) AS longitude, created_at
                    FROM public.equipment_assets
                    WHERE hospital_id::text = %s
                    ORDER BY created_at DESC
                    """,
                    (hospital_id.strip(),),
                )
                res = cursor.fetchall()
                if res:
                    return res
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unavailable: {exc}",
        ) from exc