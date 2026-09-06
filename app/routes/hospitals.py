import json
from pathlib import PurePosixPath
from uuid import UUID, uuid4

import requests
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from psycopg.errors import UniqueViolation
from psycopg.rows import tuple_row
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
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

router = APIRouter()

ALLOWED_ID_PROOF_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ============================================================================
# STAGE 1: Facility Pre-Verification (Public)
# ============================================================================
@router.post("/api/v1/facilities/verify-signup", response_model=HFRVerificationResponse)
def verify_facility_signup(data: HFRVerificationRequest):
    with get_supabase_connection() as connection:
        connection.row_factory = tuple_row
        with connection.cursor() as cursor:
            # Layer 1: Check seeded directory
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

            # Layer 2: Check for existing Sanjeevani hospital registration
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
def signup_hospital(data: HospitalSignupRequest):
    hospital_id = uuid4()
    user_id = uuid4()

    with get_supabase_connection() as connection:
        connection.row_factory = tuple_row
        with connection.cursor() as cursor:
            # Re-verify Layer 1
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

            # Re-verify Layer 2
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

    # 1. Provision Supabase Auth User (returns UUID)
    auth_user_id = _create_supabase_auth_identity(
        email=data.email,
        password=data.password,
        admin_name=data.admin_name,
    )

    # 2. Persist Database Entities
    try:
        with get_supabase_connection() as connection:
            with connection.cursor() as cursor:
                # Insert organization
                cursor.execute(
                    """
                    INSERT INTO public.hospitals (
                        hospital_id, mvp_hfr_id, hospital_name, verification_status, profile_status
                    )
                    VALUES (%s, %s, %s, 'VERIFIED', 'INCOMPLETE')
                    """,
                    (hospital_id, data.mvp_hfr_id.strip(), data.hospital_name.strip()),
                )

                # Insert user mapping
                cursor.execute(
                    """
                    INSERT INTO public.users (
                        user_id, auth_user_id, hospital_id, admin_name, user_mail, profile_completed
                    )
                    VALUES (%s, %s, %s, %s, %s, false)
                    """,
                    (user_id, auth_user_id, hospital_id, data.admin_name.strip(), data.email),
                )

                # Append audit record
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

    return HospitalSignupResponse(
        hospital_id=hospital_id,
        user_id=user_id,
        auth_user_id=auth_user_id,
        email=data.email,
        profile_status="INCOMPLETE",
        message="Account created successfully. Authenticate and complete profile setup to activate the hospital.",
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

    # Upload document to Supabase Storage using current_user UUIDs directly
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
                # 1. Register hospital wallet
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

                # 2. Register payment account
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

                # 3. Update users table with storage reference
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

                # 4. Activate hospital organization
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

                # 5. Append profile completed activity event
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

    return CompleteProfileResponse(
        hospital_id=current_user.hospital_id,
        user_id=current_user.user_id,
        profile_completed=True,
        profile_status="ACTIVE",
        message="Profile setup complete. Hospital organization is now ACTIVE and eligible for equipment sharing.",
    )


# ============================================================================
# Session Identity Verification
# ============================================================================
@router.get("/api/v1/auth/me", response_model=CurrentUserContext)
def get_authenticated_context(current_user: CurrentUserContext = Depends(get_current_user)):
    return current_user


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