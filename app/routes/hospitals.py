import json
from pathlib import PurePosixPath
from uuid import UUID, uuid4

import requests
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
# pyrefly: ignore [missing-import]
from psycopg.errors import UniqueViolation
# pyrefly: ignore [missing-import]
from psycopg.rows import dict_row, tuple_row
from pydantic import ValidationError

from app.core.config import settings
from app.core.database import get_supabase_connection
from app.core.dependencies import get_current_user
from app.schemas.hospital import (
    CompleteProfileResponse,
    CurrentUserContext,
    HFRVerificationRequest,
    HFRVerificationResponse,
    HospitalSignupRequest,
    HospitalSignupResponse,
    ProfileSetupData,
)
from app.services.email_services import (
    get_recent_notifications,
    send_transactional_notification,
)
from pydantic import BaseModel, EmailStr

router = APIRouter()

ALLOWED_ID_PROOF_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/api/v1/auth/login")
def login_user(credentials: LoginRequest):
    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "email": credentials.email,
        "password": credentials.password,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    data = response.json()
    return {
        "access_token": data["access_token"],
        "token_type": data["token_type"],
        "expires_in": data["expires_in"],
    }

# ============================================================================
# STAGE 1: Facility Pre-Verification (Public)
# ============================================================================
@router.post("/api/v1/facilities/verify-signup", response_model=HFRVerificationResponse)
def verify_facility_signup(data: HFRVerificationRequest):
    try:
        with get_supabase_connection() as connection:
            connection.row_factory = tuple_row
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT mvp_hfr_id, hospital_name
                    FROM public.abdm_mock_hfr
                    WHERE mvp_hfr_id = %s
                    """,
                    (data.mvp_hfr_id.strip(),),
                )
                record = cursor.fetchone()

                if record is None:
                    return HFRVerificationResponse(
                        verified=False,
                        directory_match=False,
                        registration_allowed=False,
                        mvp_hfr_id=data.mvp_hfr_id,
                        hospital_name=data.hospital_name,
                        message="No hospital found with this HFR ID in the government registry.",
                    )

                mvp_hfr_id, official_hospital_name = record
                names_match = (
                    official_hospital_name is not None
                    and official_hospital_name.strip().casefold() == data.hospital_name.strip().casefold()
                )

                if not names_match:
                    return HFRVerificationResponse(
                        verified=False,
                        directory_match=True,
                        registration_allowed=False,
                        mvp_hfr_id=mvp_hfr_id,
                        hospital_name=data.hospital_name,
                        message="Hospital name does not match the registered ABDM facility record.",
                    )

                cursor.execute(
                    """
                    SELECT hospital_id
                    FROM public.hospitals
                    WHERE mvp_hfr_id = %s
                    LIMIT 1
                    """,
                    (data.mvp_hfr_id.strip(),),
                )
                if cursor.fetchone() is not None:
                    return HFRVerificationResponse(
                        verified=True,
                        directory_match=True,
                        registration_allowed=False,
                        mvp_hfr_id=mvp_hfr_id,
                        hospital_name=official_hospital_name,
                        message=(
                            f"Hospital '{official_hospital_name}' already has an account at Sanjeevani. "
                            "Please contact your hospital administrator."
                        ),
                    )

            return HFRVerificationResponse(
                verified=True,
                directory_match=True,
                registration_allowed=True,
                mvp_hfr_id=mvp_hfr_id,
                hospital_name=official_hospital_name,
                message="Facility verified. Continue to account registration.",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unreachable: {exc}. Please verify SUPABASE_HOST and credentials in .env.",
        ) from exc


import math


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 4)


@router.get("/api/v1/facilities/search")
def search_facilities(
    query: str = "",
    limit: int = 20,
):
    """Searches the seeded government hospital directory (ABDM mock) by name or HFR ID."""
    clean_query = query.strip()
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                if clean_query:
                    pattern = f"%{clean_query}%"
                    cursor.execute(
                        """
                        SELECT 
                            mvp_hfr_id, hospital_name, address, latitude, longitude
                        FROM public.abdm_mock_hfr
                        WHERE hospital_name ILIKE %s OR mvp_hfr_id ILIKE %s
                        ORDER BY hospital_name ASC
                        LIMIT %s
                        """,
                        (pattern, pattern, min(max(1, limit), 100)),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT 
                            mvp_hfr_id, hospital_name, address, latitude, longitude
                        FROM public.abdm_mock_hfr
                        ORDER BY hospital_name ASC
                        LIMIT %s
                        """,
                        (min(max(1, limit), 100),),
                    )
                res = cursor.fetchall()
                if res:
                    return res
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unavailable: {exc}",
        ) from exc

    return []


# ============================================================================
# Nearby Facility & Hospital Directory (ABDM Mock Geo-Search)
# ============================================================================
@router.get("/api/v1/facilities/nearby")
@router.get("/hospitals/nearby")
def list_nearby_hospitals(
    lat: float | None = None,
    latitude: float | None = None,
    lon: float | None = None,
    longitude: float | None = None,
    lng: float | None = None,
    radius_km: float = 100.0,
    limit: int = 20,
    equipment_type: str | None = None,
):
    """
    Lists nearby hospitals from public.abdm_mock_hfr in Supabase based on latitude and longitude coordinates.
    Computes exact geographic distance (in km) and merges registered status and available equipment.
    """
    resolved_lat = latitude if latitude is not None else lat
    resolved_lon = longitude if longitude is not None else (lng if lng is not None else lon)

    if resolved_lat is None or resolved_lon is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both latitude (lat) and longitude (lon/lng) parameters are required.",
        )

    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                # Spherical Haversine calculation directly in PostgreSQL
                query = """
                SELECT 
                    m.mvp_hfr_id,
                    m.hospital_name,
                    m.address,
                    m.latitude::float8 AS latitude,
                    m.longitude::float8 AS longitude,
                    h.hospital_id::text AS hospital_id,
                    COALESCE(h.profile_status, 'UNREGISTERED') AS profile_status,
                    COALESCE(h.verification_status, 'PENDING') AS verification_status,
                    hw.address AS wallet_address,
                    (
                        6371.0 * acos(
                            least(1.0, greatest(-1.0, 
                                cos(radians(%s)) * cos(radians(m.latitude::float8)) * 
                                cos(radians(m.longitude::float8) - radians(%s)) + 
                                sin(radians(%s)) * sin(radians(m.latitude::float8))
                            ))
                        )
                    )::float8 AS distance_km
                FROM public.abdm_mock_hfr m
                LEFT JOIN public.hospitals h ON m.mvp_hfr_id = h.mvp_hfr_id
                LEFT JOIN public.hospital_wallets hw ON h.hospital_id = hw.hospital_id
                WHERE m.latitude IS NOT NULL AND m.longitude IS NOT NULL
                  AND (
                        6371.0 * acos(
                            least(1.0, greatest(-1.0, 
                                cos(radians(%s)) * cos(radians(m.latitude::float8)) * 
                                cos(radians(m.longitude::float8) - radians(%s)) + 
                                sin(radians(%s)) * sin(radians(m.latitude::float8))
                            ))
                        )
                  ) <= %s
                ORDER BY distance_km ASC
                LIMIT %s
                """
                cursor.execute(
                    query,
                    (
                        resolved_lat,
                        resolved_lon,
                        resolved_lat,
                        resolved_lat,
                        resolved_lon,
                        resolved_lat,
                        float(radius_km),
                        min(max(1, limit), 100),
                    ),
                )
                hospitals = cursor.fetchall()

                # If equipment_type filter is specified, query active equipment inventory
                if equipment_type and hospitals:
                    hospital_ids = [h["hospital_id"] for h in hospitals if h.get("hospital_id")]
                    if hospital_ids:
                        cursor.execute(
                            """
                            SELECT hospital_id::text, COUNT(asset_id)::int AS count
                            FROM public.equipment_assets
                            WHERE hospital_id::text = ANY(%s)
                              AND LOWER(equipment_type) = LOWER(%s)
                              AND availability_status = 'AVAILABLE'
                              AND shareable = true
                            GROUP BY hospital_id
                            """,
                            (hospital_ids, equipment_type.strip()),
                        )
                        eq_map = {row["hospital_id"]: row["count"] for row in cursor.fetchall()}
                        for h in hospitals:
                            h["available_equipment_count"] = eq_map.get(h.get("hospital_id"), 0)

                if hospitals:
                    return hospitals
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unavailable: {exc}",
        ) from exc

    return []


@router.get("/hospitals")
@router.get("/api/v1/organizations")
def list_hospitals():
    """Returns registered hospitals from Supabase for frontend dashboard and network queries."""
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        h.hospital_id::text AS id,
                        h.hospital_name AS name,
                        h.mvp_hfr_id,
                        h.profile_status AS status,
                        h.verification_status,
                        hw.address AS wallet,
                        COALESCE(mock.latitude, 22.5726)::float8 AS lat,
                        COALESCE(mock.longitude, 88.3639)::float8 AS lon
                    FROM public.hospitals h
                    LEFT JOIN public.hospital_wallets hw ON h.hospital_id = hw.hospital_id
                    LEFT JOIN public.abdm_mock_hfr mock ON h.mvp_hfr_id = mock.mvp_hfr_id
                    WHERE h.profile_status = 'ACTIVE' OR h.verification_status = 'VERIFIED'
                    ORDER BY h.hospital_name ASC
                    """
                )
                rows = cursor.fetchall()
                if rows:
                    return [
                        {
                            "id": r["id"],
                            "hospital_id": r["id"],
                            "name": r["name"],
                            "hospital_name": r["name"],
                            "mvp_hfr_id": r["mvp_hfr_id"],
                            "status": r["status"],
                            "wallet": r.get("wallet") or "",
                            "location": {
                                "lat": r["lat"],
                                "lon": r["lon"],
                            },
                        }
                        for r in rows
                    ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unavailable: {exc}",
        ) from exc

    return []


@router.get("/hospitals/{hospital_id}")
@router.get("/api/v1/organizations/{hospital_id}")
def get_hospital_details(hospital_id: str):
    """Returns details for a specific registered hospital from Supabase."""
    try:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        h.hospital_id::text AS id,
                        h.hospital_name AS name,
                        h.mvp_hfr_id,
                        h.profile_status AS status,
                        h.verification_status,
                        hw.address AS wallet,
                        COALESCE(mock.latitude, 22.5726)::float8 AS lat,
                        COALESCE(mock.longitude, 88.3639)::float8 AS lon
                    FROM public.hospitals h
                    LEFT JOIN public.hospital_wallets hw ON h.hospital_id = hw.hospital_id
                    LEFT JOIN public.abdm_mock_hfr mock ON h.mvp_hfr_id = mock.mvp_hfr_id
                    WHERE h.hospital_id::text = %s OR h.mvp_hfr_id = %s
                    LIMIT 1
                    """,
                    (hospital_id, hospital_id),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "hospital_id": row["id"],
                        "name": row["name"],
                        "hospital_name": row["name"],
                        "mvp_hfr_id": row["mvp_hfr_id"],
                        "status": row["status"],
                        "wallet": row.get("wallet") or "",
                        "location": {
                            "lat": row["lat"],
                            "lon": row["lon"],
                        },
                    }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase database unavailable: {exc}",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Hospital was not found in Supabase.",
    )


class HospitalRegistrationRequest(BaseModel):
    admin_name: str
    email: EmailStr | str
    hospital_name: str
    mvp_hfr_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    address: str | None = None


@router.post("/hospitals", status_code=status.HTTP_201_CREATED)
@router.post("/api/v1/auth/register-hospital-admin", status_code=status.HTTP_201_CREATED)
def register_hospital_and_admin(data: HospitalRegistrationRequest, background_tasks: BackgroundTasks):
    """
    Registers a hospital and administrator directly into Supabase (public.hospitals & public.users),
    verifies with ABDM mock HFR in Supabase, and dispatches an onboarding welcome email.
    """
    hospital_id = uuid4()
    user_id = uuid4()
    auth_user_id = uuid4()

    # Determine HFR ID and verify coordinates against Supabase public.abdm_mock_hfr
    resolved_hfr_id = (data.mvp_hfr_id or "").strip()
    lat = data.latitude
    lon = data.longitude

    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            if not resolved_hfr_id:
                cursor.execute(
                    """
                    SELECT mvp_hfr_id, hospital_name, latitude, longitude
                    FROM public.abdm_mock_hfr
                    WHERE LOWER(hospital_name) = LOWER(%s)
                    LIMIT 1
                    """,
                    (data.hospital_name.strip(),),
                )
                match = cursor.fetchone()
                if match:
                    resolved_hfr_id = match["mvp_hfr_id"]
                    if lat is None:
                        lat = match["latitude"]
                    if lon is None:
                        lon = match["longitude"]
                else:
                    resolved_hfr_id = f"HFR-{uuid4().hex[:8].upper()}"

            if lat is None or lon is None:
                cursor.execute(
                    "SELECT latitude, longitude FROM public.abdm_mock_hfr WHERE mvp_hfr_id = %s LIMIT 1",
                    (resolved_hfr_id,),
                )
                hfr_row = cursor.fetchone()
                if hfr_row and hfr_row.get("latitude") is not None:
                    lat = float(hfr_row["latitude"])
                    lon = float(hfr_row["longitude"])
                else:
                    lat = lat or 11.6358
                    lon = lon or 92.7121

            # Persist hospital and admin user in Supabase PostgreSQL
            cursor.execute(
                """
                INSERT INTO public.hospitals (
                    hospital_id, mvp_hfr_id, hospital_name, verification_status, profile_status
                )
                VALUES (%s, %s, %s, 'VERIFIED', 'ACTIVE')
                ON CONFLICT (hospital_id) DO NOTHING
                """,
                (hospital_id, resolved_hfr_id, data.hospital_name.strip()),
            )
            cursor.execute(
                """
                INSERT INTO public.users (
                    user_id, auth_user_id, hospital_id, admin_name, user_mail, profile_completed
                )
                VALUES (%s, %s, %s, %s, %s, true)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (user_id, auth_user_id, hospital_id, data.admin_name.strip(), str(data.email).strip()),
            )
            connection.commit()

    # Dispatch welcome email
    welcome_html = f"""
    <h2>Welcome to SANJEEVANI</h2>
    <p>Dear {data.admin_name},</p>
    <p>Your hospital organization <strong>{data.hospital_name}</strong> (ABDM HFR: {resolved_hfr_id}) has been successfully registered on the SANJEEVANI network.</p>
    <p>You can now list medical equipment in the network inventory, discover nearby hospital partners, and sanction equipment transactions with smart care workflows.</p>
    <ul>
        <li><strong>Hospital ID:</strong> {hospital_id}</li>
        <li><strong>Administrator:</strong> {data.admin_name} ({data.email})</li>
        <li><strong>Status:</strong> VERIFIED & ACTIVE</li>
    </ul>
    """
    background_tasks.add_task(
        send_transactional_notification,
        hospital_id=hospital_id,
        recipient_email=str(data.email).strip(),
        event_type="ACCOUNT_REGISTERED",
        subject=f"Welcome to SANJEEVANI — {data.hospital_name} Registered",
        html_content=welcome_html,
    )

    return {
        "success": True,
        "hospital_id": str(hospital_id),
        "user_id": str(user_id),
        "hospital_name": data.hospital_name.strip(),
        "admin_name": data.admin_name.strip(),
        "admin_email": str(data.email).strip(),
        "mvp_hfr_id": resolved_hfr_id,
        "status": "ACTIVE",
        "message": "Hospital administrator and organization registered successfully. Welcome email dispatched.",
    }


@router.get("/notifications")
@router.get("/api/v1/notifications")
def list_recent_notifications(limit: int = 50):
    """Returns recent sent email notification logs from Supabase or memory buffer."""
    return get_recent_notifications(limit=limit)


# ============================================================================
# STAGE 2: Auth User & Organization Account Signup (Public)
# ============================================================================
def _create_supabase_auth_identity(email: str, password: str, admin_name: str) -> UUID:
    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"admin_name": admin_name},
    }

    response = requests.post(url, headers=headers, json=payload, timeout=15)
    if response.status_code in (400, 422):
        err_detail = response.json().get("msg") or response.json().get("message") or "Email already registered."
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_detail)
    if response.status_code >= 300:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to provision Supabase Auth identity: {response.text}",
        )

    return UUID(response.json()["id"])


def _rollback_supabase_auth_identity(auth_user_id: UUID | str) -> None:
    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users/{auth_user_id}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
    }
    try:
        requests.delete(url, headers=headers, timeout=10)
    except requests.RequestException:
        pass


@router.post(
    "/api/v1/auth/signup",
    response_model=HospitalSignupResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup_hospital(data: HospitalSignupRequest, background_tasks: BackgroundTasks):
    hospital_id = uuid4()
    user_id = uuid4()

    with get_supabase_connection() as connection:
        connection.row_factory = tuple_row
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT mvp_hfr_id, hospital_name
                FROM public.abdm_mock_hfr
                WHERE mvp_hfr_id = %s
                """,
                (data.mvp_hfr_id.strip(),),
            )
            mock_record = cursor.fetchone()
            if (
                mock_record is None
                or mock_record[1] is None
                or mock_record[1].strip().casefold() != data.hospital_name.strip().casefold()
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="HFR ID and hospital name could not be verified against the government directory.",
                )

            cursor.execute(
                """
                SELECT hospital_id
                FROM public.hospitals
                WHERE mvp_hfr_id = %s
                LIMIT 1
                """,
                (data.mvp_hfr_id.strip(),),
            )
            if cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This hospital already has a registered organization at Sanjeevani.",
                )

    auth_user_id = _create_supabase_auth_identity(
        email=data.email,
        password=data.password,
        admin_name=data.admin_name,
    )

    try:
        with get_supabase_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.hospitals (
                        hospital_id, mvp_hfr_id, hospital_name, verification_status, profile_status
                    )
                    VALUES (%s, %s, %s, 'VERIFIED', 'INCOMPLETE')
                    """,
                    (hospital_id, data.mvp_hfr_id.strip(), data.hospital_name.strip()),
                )

                cursor.execute(
                    """
                    INSERT INTO public.users (
                        user_id, auth_user_id, hospital_id, admin_name, user_mail, profile_completed
                    )
                    VALUES (%s, %s, %s, %s, %s, false)
                    """,
                    (user_id, auth_user_id, hospital_id, data.admin_name.strip(), data.email),
                )

                cursor.execute(
                    """
                    INSERT INTO public.activity_events (
                        activity_id, hospital_id, user_id, entity_type, entity_id, event_type, metadata
                    )
                    VALUES (%s, %s, %s, 'ORGANIZATION', %s, 'organization.created', %s)
                    """,
                    (
                        uuid4(),
                        hospital_id,
                        user_id,
                        hospital_id,
                        json.dumps({
                            "hospital_name": data.hospital_name.strip(),
                            "mvp_hfr_id": data.mvp_hfr_id.strip(),
                        }),
                    ),
                )

                connection.commit()
    except Exception as exc:
        _rollback_supabase_auth_identity(auth_user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization failed: {exc}",
        ) from exc

    # Queue welcome email
    welcome_html = f"""
    <h2>Welcome to SANJEEVANI</h2>
    <p>Dear {data.admin_name},</p>
    <p>Your hospital organization <strong>{data.hospital_name}</strong> (HFR: {data.mvp_hfr_id}) has been registered.</p>
    <p>Please log in and complete your profile setup (EVM wallet, UPI account, and administrator verification) to activate equipment sharing.</p>
    """
    background_tasks.add_task(
        send_transactional_notification,
        hospital_id=hospital_id,
        recipient_email=data.email,
        event_type="ACCOUNT_REGISTERED",
        subject="Welcome to SANJEEVANI — Account Registered",
        html_content=welcome_html,
    )

    return HospitalSignupResponse(
        hospital_id=hospital_id,
        user_id=user_id,
        auth_user_id=auth_user_id,
        email=data.email,
        profile_status="INCOMPLETE",
        message="Account created successfully. Complete profile setup to activate the hospital.",
    )


# ============================================================================
# STAGE 3: Profile Setup Gate (Protected: Requires Bearer JWT)
# ============================================================================
def _upload_storage_document(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    hospital_id: UUID | str,
    auth_user_id: UUID | str,
) -> str:
    if not settings.SUPABASE_SERVICE_ROLE_KEY or not settings.SUPABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Storage credentials are not configured on the server.",
        )

    clean_filename = PurePosixPath(filename or "identity-proof").name
    object_path = f"{hospital_id}/{auth_user_id}/{clean_filename}"
    url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{object_path}"

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Content-Type": content_type or "application/octet-stream",
            "x-upsert": "false",
        },
        data=file_bytes,
        timeout=30,
    )
    if response.status_code >= 300:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Supabase Storage rejected identity document upload: {response.text}",
        )
    return object_path


@router.post(
    "/api/v1/organizations/me/complete-profile",
    response_model=CompleteProfileResponse,
)
def complete_hospital_profile(
    background_tasks: BackgroundTasks,
    wallet_address: str = Form(...),
    network: str = Form(...),
    upi_id: str = Form(...),
    provider: str = Form(...),
    user_id_proof: UploadFile = File(...),
    current_user: CurrentUserContext = Depends(get_current_user),
):
    if current_user.profile_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile is already verified and active.",
        )

    try:
        profile_data = ProfileSetupData(
            wallet_address=wallet_address,
            network=network,
            upi_id=upi_id,
            provider=provider,
        )
    except ValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err.errors(),
        ) from err

    if user_id_proof.content_type not in ALLOWED_ID_PROOF_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file MIME type '{user_id_proof.content_type}'. Allowed types: PDF, JPEG, PNG, WEBP.",
        )

    file_bytes = user_id_proof.file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document size exceeds 10 MB limit.",
        )

    wallet_id = uuid4()
    payment_account_id = uuid4()

    proof_reference = _upload_storage_document(
        file_bytes=file_bytes,
        filename=user_id_proof.filename or "identity-proof",
        content_type=user_id_proof.content_type or "application/octet-stream",
        hospital_id=current_user.hospital_id,
        auth_user_id=current_user.auth_user_id,
    )

    with get_supabase_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO public.hospital_wallets (
                        wallet_id, hospital_id, address, network, verified
                    )
                    VALUES (%s, %s, %s, %s, false)
                    """,
                    (
                        wallet_id,
                        current_user.hospital_id,
                        profile_data.wallet_address,
                        profile_data.network,
                    ),
                )

                cursor.execute(
                    """
                    INSERT INTO public.hospital_payment_accounts (
                        payment_account_id, hospital_id, provider, upi_id, verification_status, is_active
                    )
                    VALUES (%s, %s, %s, %s, 'PENDING', true)
                    """,
                    (
                        payment_account_id,
                        current_user.hospital_id,
                        profile_data.provider,
                        profile_data.upi_id,
                    ),
                )

                cursor.execute(
                    """
                    UPDATE public.users
                    SET 
                        id_proof_reference = %s,
                        profile_completed = true,
                        updated_at = now()
                    WHERE user_id = %s
                    """,
                    (proof_reference, current_user.user_id),
                )

                cursor.execute(
                    """
                    UPDATE public.hospitals
                    SET 
                        profile_status = 'ACTIVE',
                        updated_at = now()
                    WHERE hospital_id = %s
                    """,
                    (current_user.hospital_id,),
                )

                cursor.execute(
                    """
                    INSERT INTO public.activity_events (
                        activity_id, hospital_id, user_id, entity_type, entity_id, event_type, metadata
                    )
                    VALUES (%s, %s, %s, 'ORGANIZATION', %s, 'organization.profile_completed', %s)
                    """,
                    (
                        uuid4(),
                        current_user.hospital_id,
                        current_user.user_id,
                        current_user.hospital_id,
                        json.dumps({
                            "wallet_address": profile_data.wallet_address,
                            "network": profile_data.network,
                            "upi_provider": profile_data.provider,
                        }),
                    ),
                )

                connection.commit()
            except UniqueViolation as exc:
                connection.rollback()
                diag_msg = str(exc).lower()
                if "address" in diag_msg or "hospital_wallets_address_key" in diag_msg:
                    detail = "This blockchain wallet address is already linked to another hospital."
                else:
                    detail = "A collision occurred on a unique hospital profile field."
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
            except Exception as exc:
                connection.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Profile completion failed: {exc}",
                ) from exc

    # Queue profile completed confirmation email
    activation_html = f"""
    <h2>SANJEEVANI — Hospital Profile Activated</h2>
    <p>Dear {current_user.admin_name},</p>
    <p>The profile for <strong>{current_user.hospital_name}</strong> is now verified and <strong>ACTIVE</strong>.</p>
    <p>Your hospital is now eligible to list medical equipment and participate in resource sharing.</p>
    <ul>
        <li><strong>Registered EVM Wallet:</strong> {profile_data.wallet_address}</li>
        <li><strong>UPI Account:</strong> {profile_data.upi_id} ({profile_data.provider})</li>
    </ul>
    """
    background_tasks.add_task(
        send_transactional_notification,
        hospital_id=current_user.hospital_id,
        recipient_email=current_user.user_mail,
        event_type="PROFILE_COMPLETED",
        subject="SANJEEVANI — Hospital Profile Activated",
        html_content=activation_html,
    )

    return CompleteProfileResponse(
        hospital_id=current_user.hospital_id,
        user_id=current_user.user_id,
        profile_completed=True,
        profile_status="ACTIVE",
        message="Profile setup complete. Hospital organization is now ACTIVE and eligible for equipment sharing.",
    )