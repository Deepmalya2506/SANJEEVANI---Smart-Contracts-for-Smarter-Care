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
    Executes the 5-stage GIS pipeline for equipment dispatch:
    1. Spatial Query: PostGIS ST_DWithin bounding filter in PostgreSQL.
    2. Hex Pruning: Uber H3 candidate grouping.
    3. Road Routing: OSRM driving geometry and distance.
    4. Traffic Mask: Real-time congestion status and speed penalties.
    5. Feasibility Ranking: Production of approval-guarded proposal.
    """
    equipment_type = str(request_data["equipment_type"]).strip()
    quantity = int(request_data.get("quantity", 1))
    origin = {
        "lat": float(request_data["location"]["lat"]),
        "lon": float(request_data["location"]["lon"]),
    }
    max_eta = int(request_data.get("max_eta_minutes", 60))
    requesting_hospital_id = request_data.get("from_hospital_id")

    # Bounding radius: conservative 1km per minute ETA, minimum 35km bounding radius
    search_radius_meters = max(float(max_eta) * 1000.0, 35000.0)

    # Step 1: PostGIS ST_DWithin spatial query on Supabase PostgreSQL
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
                    AVG(ea.hourly_rate)::float8 AS avg_hourly_rate,
                    MIN(
                        ST_Distance(
                            COALESCE(ea.location, ST_SetSRID(ST_MakePoint(mock.longitude, mock.latitude), 4326))::geography,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                        )
                    )::float8 AS spatial_distance_m
                FROM public.equipment_assets ea
                JOIN public.hospitals h ON ea.hospital_id = h.hospital_id
                LEFT JOIN public.abdm_mock_hfr mock ON h.mvp_hfr_id = mock.mvp_hfr_id
                LEFT JOIN public.hospital_wallets hw ON h.hospital_id = hw.hospital_id
                WHERE LOWER(ea.equipment_type) = LOWER(%s)
                  AND ea.availability_status = 'AVAILABLE'
                  AND ea.shareable = true
                  AND h.profile_status = 'ACTIVE'
                  AND (%s::uuid IS NULL OR h.hospital_id <> %s::uuid)
                  AND ST_DWithin(
                      COALESCE(ea.location, ST_SetSRID(ST_MakePoint(mock.longitude, mock.latitude), 4326))::geography,
                      ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                      %s
                  )
                GROUP BY h.hospital_id, h.hospital_name, hw.address
                HAVING COUNT(ea.asset_id) >= %s
                ORDER BY spatial_distance_m ASC
                """,
                (
                    origin["lon"],
                    origin["lat"],
                    equipment_type,
                    requesting_hospital_id,
                    requesting_hospital_id,
                    origin["lon"],
                    origin["lat"],
                    search_radius_meters,
                    quantity,
                ),
            )
            candidate_hospitals = cursor.fetchall()

            # If no candidates within tight radius, try a broader regional search
            if not candidate_hospitals:
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
                    LIMIT 10
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
            "message": f"No active hospitals found with {quantity} available '{equipment_type}' units within reachable radius.",
        }

    gis_candidates = [
        h for h in candidate_hospitals
        if h["latitude"] is not None and h["longitude"] is not None
    ]

    if not gis_candidates:
        return {
            "status": "LOCATION_ERROR",
            "message": "Candidate hospitals do not have valid geospatial coordinates registered.",
        }

    # Step 2, 3, 4: Call GIS Engine for H3 Pruning, OSRM Routing, and Traffic Masking
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

    best_candidate = next(
        (h for h in gis_candidates if str(h["hospital_id"]) == str(best_hospital_id)),
        gis_candidates[0],
    )

    # Step 5: Produce Ranked Proposal
    best_opt = best_data.get("best_option", {})
    proposal = {
        "status": "PROPOSED",
        "selected_hospital": {
            "hospital_id": str(best_candidate["hospital_id"]),
            "hospital_name": best_candidate["hospital_name"],
            "wallet_address": best_candidate.get("wallet_address"),
            "available_units": best_candidate["available_count"],
            "avg_hourly_rate": best_candidate["avg_hourly_rate"],
        },
        "gis_feasibility": {
            "origin": origin,
            "eta_min": best_opt.get("traffic_adjusted_eta_min", best_data.get("eta_min")),
            "baseline_eta_min": best_opt.get("baseline_eta_min"),
            "distance_km": best_opt.get("distance_km", best_data.get("distance_km")),
            "traffic_status": best_opt.get("traffic_status", "NORMAL"),
            "traffic_color": best_opt.get("traffic_color", "#10B981"),
            "h3_cell": best_opt.get("h3_cell"),
            "feasible": best_opt.get("feasible", True),
            "route_geometry": best_opt.get("route_geometry"),
            "h3_coverage": best_data.get("h3_coverage"),
            "all_options": best_data.get("all_options", []),
        },
        "requires_approval": True,
    }

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