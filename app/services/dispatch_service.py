from typing import Any
from uuid import UUID
from psycopg.rows import dict_row

from app.core.database import get_supabase_connection
from app.services.gis_client import get_best_option

# Optional blockchain import with fallback
try:
    from app.services.blockchain_client import create_loan
except ImportError:
    create_loan = None


def dispatch_logic(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    1. Queries PostgreSQL for active hospitals with shareable, available assets.
    2. Sends geographic coordinates and candidates to the GIS routing engine.
    3. Formulates the ranked feasibility proposal according to the build plan.
    """
    equipment_type = str(request_data["equipment_type"]).strip()
    quantity = int(request_data.get("quantity", 1))
    origin = {
        "lat": float(request_data["location"]["lat"]),
        "lon": float(request_data["location"]["lon"]),
    }
    max_eta = int(request_data.get("max_eta_minutes", 60))
    requesting_hospital_id = request_data.get("from_hospital_id")

    # Step 1: Query Supabase PostgreSQL for eligible candidate hospitals
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT 
                    h.hospital_id,
                    h.hospital_name,
                    hw.address AS wallet_address,
                    COUNT(ea.asset_id)::int AS available_count,
                    COALESCE(
                        AVG(ST_Y(ea.location)), 
                        AVG(mock.latitude)
                    )::float8 AS latitude,
                    COALESCE(
                        AVG(ST_X(ea.location)), 
                        AVG(mock.longitude)
                    )::float8 AS longitude,
                    AVG(ea.hourly_rate)::float8 AS avg_hourly_rate
                FROM public.equipment_assets ea
                JOIN public.hospitals h ON ea.hospital_id = h.hospital_id
                LEFT JOIN public.abdm_mock_hfr mock ON h.mvp_hfr_id = mock.mvp_hfr_id
                LEFT JOIN public.hospital_wallets hw ON h.hospital_id = hw.hospital_id
                WHERE LOWER(ea.equipment_type) = LOWER(%s)
                  AND ea.availability_status = 'AVAILABLE'
                  AND ea.shareable = true
                  AND h.profile_status = 'ACTIVE'
                  AND (%s::uuid IS NULL OR h.hospital_id <> %s::uuid)
                GROUP BY h.hospital_id, h.hospital_name, hw.address
                HAVING COUNT(ea.asset_id) >= %s
                """,
                (
                    equipment_type,
                    requesting_hospital_id,
                    requesting_hospital_id,
                    quantity,
                ),
            )
            candidate_hospitals = cursor.fetchall()

    if not candidate_hospitals:
        return {
            "status": "NO_CANDIDATES",
            "message": f"No active hospitals found with {quantity} available '{equipment_type}' units.",
        }

    # Filter candidates with valid spatial coordinates
    gis_candidates = [
        h for h in candidate_hospitals
        if h["latitude"] is not None and h["longitude"] is not None
    ]

    if not gis_candidates:
        return {
            "status": "LOCATION_ERROR",
            "message": "Candidate hospitals do not have valid geospatial coordinates registered.",
        }

    # Step 2: Query GIS Engine for routing and traffic feasibility
    gis_response = get_best_option(
        origin=origin,
        hospitals=gis_candidates,
        max_eta_minutes=max_eta,
    )

    if "error" in gis_response:
        return {
            "status": "GIS_ERROR",
            "error": f"GIS service routing failure: {gis_response.get('error')}",
            "detail": gis_response.get("detail"),
        }

    best_data = gis_response.get("data", gis_response)
    best_hospital_id = best_data.get("best_hospital")

    # Match GIS selection with database candidate record
    best_candidate = next(
        (h for h in gis_candidates if str(h["hospital_id"]) == str(best_hospital_id)),
        None,
    )

    if best_candidate is None:
        # Fallback to the first candidate if GIS returned an alternative identifier
        best_candidate = gis_candidates[0]

    # Step 3: Produce Loan Proposal (Guarded by User Approval per Build Plan)
    proposal = {
        "status": "PROPOSED",
        "selected_hospital": {
            "hospital_id": str(best_candidate["hospital_id"]),
            "hospital_name": best_candidate["hospital_name"],
            "wallet_address": best_candidate.get("wallet_address"),
            "available_units": best_candidate["available_count"],
            "avg_hourly_rate": best_candidate["avg_hourly_rate"],
        },
        "gis_feasibility": best_data,
        "requires_approval": True,
    }

    # Optional immediate contract submission if bypass flag is explicitly enabled
    if not request_data.get("skip_blockchain", True) and create_loan is not None:
        loan_result = create_loan({
            "lender": best_candidate.get("wallet_address"),
            "equipment_type": equipment_type,
            "quantity": quantity,
            "duration": request_data.get("duration_hours", 24),
            "value": 0,
        })
        proposal["loan_commitment"] = loan_result

    return proposal