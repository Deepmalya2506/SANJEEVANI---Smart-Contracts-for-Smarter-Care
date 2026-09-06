"""This dependency validates the incoming Bearer JWT against Supabase Auth and queries the operational schema to bind the request to the caller's organization."""

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg.rows import tuple_row

from app.core.config import settings
from app.core.database import get_supabase_connection
from app.schemas.hospital import CurrentUserContext

# Enables the Swagger UI "Authorize" button
security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> CurrentUserContext:
    token = credentials.credentials.strip()

    # Validate session token with Supabase Auth
    verify_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
    }

    try:
        response = requests.get(verify_url, headers=headers, timeout=10)
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase Auth gateway unreachable: {exc}",
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is invalid or expired.",
        )

    auth_user_id = response.json()["id"]

    # Resolve organization binding
    with get_supabase_connection() as connection:
        connection.row_factory = tuple_row
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    u.user_id, 
                    u.auth_user_id, 
                    u.hospital_id, 
                    u.admin_name, 
                    u.user_mail,
                    u.profile_completed, 
                    h.hospital_name, 
                    h.mvp_hfr_id, 
                    h.profile_status, 
                    h.verification_status
                FROM public.users u
                JOIN public.hospitals h ON u.hospital_id = h.hospital_id
                WHERE u.auth_user_id = %s
                LIMIT 1
                """,
                (auth_user_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No registered hospital organization found for this authenticated user.",
                )

            return CurrentUserContext(
                user_id=row[0],
                auth_user_id=row[1],
                hospital_id=row[2],
                admin_name=row[3],
                user_mail=row[4],
                profile_completed=row[5],
                hospital_name=row[6],
                mvp_hfr_id=row[7],
                profile_status=row[8],
                verification_status=row[9],
            )


