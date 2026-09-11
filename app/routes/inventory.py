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

    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                hospital_id, user_id, admin_name, user_mail, mvp_hfr_id = _resolve_hospital_and_admin(
                    cursor, data.hospital_id, request
                )

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
            detail=f"Supabase database unreachable: {exc}. Please verify SUPABASE_HOST and credentials in .env.",
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
    request: Request,
    background_tasks: BackgroundTasks,
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
                            FOR UPDATE
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
                        FOR UPDATE
                        """,
                        (lender_hospital_id, data.equipment_type.strip()),
                    )
                    asset_record = cursor.fetchone()

                resolved_asset_id = asset_record["asset_id"] if asset_record else uuid4()

                # 4. Lock asset to RESERVED if found
                if asset_record:
                    cursor.execute(
                        """
                        UPDATE public.equipment_assets
                        SET availability_status = 'RESERVED', updated_at = now()
                        WHERE asset_id = %s
                        """,
                        (resolved_asset_id,),
                    )

                # 5. Create or sanction loan entry
                loan_id = uuid4()
                cursor.execute(
                    """
                    INSERT INTO public.loans (
                        loan_id, asset_id, lender_hospital_id, borrower_hospital_id,
                        loan_status, duration_hours, notes
                    )
                    VALUES (%s, %s, %s, %s, 'APPROVED', %s, %s)
                    """,
                    (
                        loan_id,
                        resolved_asset_id,
                        lender_hospital_id,
                        borrower_hospital_id,
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
                for contact in admin_contacts:
                    if contact.get("user_mail"):
                        sanction_email = f"""
                        <h2>SANJEEVANI — Equipment Transaction Sanctioned</h2>
                        <p>Dear {contact.get('admin_name', 'Administrator')},</p>
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
                        background_tasks.add_task(
                            send_transactional_notification,
                            hospital_id=borrower_hospital_id,
                            recipient_email=contact["user_mail"],
                            event_type="TRANSACTION_SANCTIONED",
                            subject=f"SANJEEVANI — Transaction Sanctioned: {data.equipment_type}",
                            html_content=sanction_email,
                            loan_id=loan_id,
                        )

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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unreachable: {exc}. Please verify SUPABASE_HOST and credentials in .env.",
        ) from exc



EQUIPMENT_NUMERIC_MAP = {
    "1": "Oxygen concentrator",
    "2": "Portable ventilator",
    "3": "Patient monitor",
    "4": "Infusion pump",
}

@router.get("/inventory/search", response_model=list[HospitalInventoryGroup])
@router.get("/api/v1/inventory/search", response_model=list[HospitalInventoryGroup])
def search_inventory(
    equipment_type: str = Query(..., min_length=1),
    quantity: int = Query(default=1, gt=0),
):
    clean_type = equipment_type.strip()
    resolved_type = EQUIPMENT_NUMERIC_MAP.get(clean_type, clean_type)

    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
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
                      AND h.profile_status = 'ACTIVE'
                    GROUP BY ea.hospital_id, h.hospital_name, ea.equipment_type
                    HAVING COUNT(ea.asset_id) >= %s
                    ORDER BY available_count DESC
                    """,
                    (clean_type, resolved_type, quantity),
                )
                return cursor.fetchall()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unreachable: {exc}. Please verify SUPABASE_HOST and credentials in .env.",
        ) from exc


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
                return cursor.fetchall()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unreachable: {exc}. Please verify SUPABASE_HOST and credentials in .env.",
        ) from exc