import io
import json
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
import pandas as pd
from psycopg.rows import dict_row

from app.core.database import get_supabase_connection
from app.core.dependencies import get_current_user
from app.schemas.hospital import CurrentUserContext
from app.schemas.inventory import (
    EquipmentAssetCreate,
    EquipmentAssetResponse,
    HospitalInventoryGroup,
)

router = APIRouter()


@router.post(
    "/api/v1/equipment/assets",
    response_model=EquipmentAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_equipment_asset(
    data: EquipmentAssetCreate,
    current_user: CurrentUserContext = Depends(get_current_user),
):
    asset_id = uuid4()

    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            lat = data.latitude
            lon = data.longitude

            # Fallback to ABDM directory coordinates if asset location is not provided
            if lat is None or lon is None:
                cursor.execute(
                    """
                    SELECT latitude, longitude 
                    FROM public.abdm_mock_hfr 
                    WHERE mvp_hfr_id = %s
                    """,
                    (current_user.mvp_hfr_id,),
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
                    current_user.hospital_id,
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
                    current_user.hospital_id,
                    current_user.user_id,
                    asset_id,
                    json.dumps({
                        "name": data.name,
                        "equipment_type": data.equipment_type,
                    }),
                ),
            )
            connection.commit()

    if created_asset is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register equipment asset.",
        )

    return created_asset


@router.post("/api/v1/inventory/upload", status_code=status.HTTP_201_CREATED)
async def upload_inventory_csv(
    file: UploadFile = File(...),
    current_user: CurrentUserContext = Depends(get_current_user),
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

    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            # Fallback coordinates from hospital registry record
            cursor.execute(
                """
                SELECT latitude, longitude 
                FROM public.abdm_mock_hfr 
                WHERE mvp_hfr_id = %s
                """,
                (current_user.mvp_hfr_id,),
            )
            hfr_row = cursor.fetchone()
            default_lat = float(hfr_row["latitude"]) if hfr_row and hfr_row["latitude"] is not None else None
            default_lon = float(hfr_row["longitude"]) if hfr_row and hfr_row["longitude"] is not None else None

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
                        current_user.hospital_id,
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

    return {
        "status": "success",
        "message": f"Successfully ingested {inserted_count} equipment assets into your inventory.",
    }


@router.get("/api/v1/inventory/search", response_model=list[HospitalInventoryGroup])
def search_inventory(
    equipment_type: str = Query(..., min_length=1),
    quantity: int = Query(default=1, gt=0),
):
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
                WHERE LOWER(ea.equipment_type) = LOWER(%s)
                  AND ea.availability_status = 'AVAILABLE'
                  AND ea.shareable = true
                  AND h.profile_status = 'ACTIVE'
                GROUP BY ea.hospital_id, h.hospital_name, ea.equipment_type
                HAVING COUNT(ea.asset_id) >= %s
                ORDER BY available_count DESC
                """,
                (equipment_type.strip(), quantity),
            )
            return cursor.fetchall()


@router.get("/api/v1/inventory/{hospital_id}", response_model=list[EquipmentAssetResponse])
def get_hospital_inventory(hospital_id: UUID):
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT 
                    asset_id, hospital_id, equipment_type, name, serial_number,
                    condition_status, availability_status, shareable, hourly_rate,
                    ST_Y(location) AS latitude, ST_X(location) AS longitude, created_at
                FROM public.equipment_assets
                WHERE hospital_id = %s
                ORDER BY created_at DESC
                """,
                (hospital_id,),
            )
            return cursor.fetchall()