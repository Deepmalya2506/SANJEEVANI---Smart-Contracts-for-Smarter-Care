from typing import Any
from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

from app.core.database import get_supabase_connection
from app.services import gis_client
from GIS_engine.services.h3_service import latlng_to_h3

router = APIRouter(prefix="/api/v1/gis", tags=["GIS"])

class Coordinate(BaseModel):
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)

class CandidatesSearchRequest(BaseModel):
    origin: Coordinate
    equipment_type: str = Field(min_length=1)
    radius_km: float = Field(default=35.0, gt=0.0, le=500.0)
    max_eta_minutes: int = Field(default=60, gt=0)

class RouteCalculationRequest(BaseModel):
    source: Coordinate
    destination: Coordinate

@router.get("/network-nodes")
def get_network_nodes():
    """
    Returns all active verified hospitals across the network with their
    PostGIS coordinates, H3 cell indexes, and live inventory asset summaries.
    Used by the /map Full Geospatial Command View.
    """
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT 
                    h.hospital_id,
                    h.hospital_name,
                    h.verification_status,
                    h.profile_status,
                    hw.address AS wallet_address,
                    hpa.upi_id,
                    COALESCE(
                        AVG(ST_Y(ea.location)), 
                        AVG(mock.latitude)
                    )::float8 AS latitude,
                    COALESCE(
                        AVG(ST_X(ea.location)), 
                        AVG(mock.longitude)
                    )::float8 AS longitude,
                    COUNT(ea.asset_id)::int AS total_assets,
                    COUNT(CASE WHEN ea.availability_status = 'AVAILABLE' THEN 1 END)::int AS available_assets,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'equipment_type', ea.equipment_type,
                                'name', ea.name,
                                'status', ea.availability_status,
                                'hourly_rate', ea.hourly_rate
                            )
                        ) FILTER (WHERE ea.asset_id IS NOT NULL),
                        '[]'::json
                    ) AS inventory_preview
                FROM public.hospitals h
                LEFT JOIN public.abdm_mock_hfr mock ON h.mvp_hfr_id = mock.mvp_hfr_id
                LEFT JOIN public.equipment_assets ea ON h.hospital_id = ea.hospital_id
                LEFT JOIN public.hospital_wallets hw ON h.hospital_id = hw.hospital_id
                LEFT JOIN public.hospital_payment_accounts hpa ON h.hospital_id = hpa.hospital_id
                WHERE h.profile_status = 'ACTIVE'
                GROUP BY h.hospital_id, h.hospital_name, h.verification_status, h.profile_status, hw.address, hpa.upi_id
                """
            )
            rows = cursor.fetchall()

    nodes = []
    for r in rows:
        lat = r["latitude"]
        lon = r["longitude"]
        if lat is not None and lon is not None:
            nodes.append({
                "hospital_id": str(r["hospital_id"]),
                "hospital_name": r["hospital_name"],
                "latitude": lat,
                "longitude": lon,
                "h3_cell": latlng_to_h3(lat, lon, 7),
                "wallet_address": r.get("wallet_address"),
                "upi_id": r.get("upi_id"),
                "total_assets": r["total_assets"],
                "available_assets": r["available_assets"],
                "inventory": r["inventory_preview"],
            })

    return {
        "status": "success",
        "count": len(nodes),
        "nodes": nodes,
    }

@router.post("/candidates")
def search_spatial_candidates(req: CandidatesSearchRequest):
    """
    Stage 1: PostGIS ST_DWithin bounding radius query around origin coordinate.
    """
    radius_meters = req.radius_km * 1000.0
    with get_supabase_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT 
                    h.hospital_id,
                    h.hospital_name,
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
                    )::float8 AS distance_meters
                FROM public.equipment_assets ea
                JOIN public.hospitals h ON ea.hospital_id = h.hospital_id
                LEFT JOIN public.abdm_mock_hfr mock ON h.mvp_hfr_id = mock.mvp_hfr_id
                WHERE LOWER(ea.equipment_type) = LOWER(%s)
                  AND ea.availability_status = 'AVAILABLE'
                  AND ea.shareable = true
                  AND h.profile_status = 'ACTIVE'
                  AND ST_DWithin(
                      COALESCE(ea.location, ST_SetSRID(ST_MakePoint(mock.longitude, mock.latitude), 4326))::geography,
                      ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                      %s
                  )
                GROUP BY h.hospital_id, h.hospital_name
                ORDER BY distance_meters ASC
                """,
                (
                    req.origin.lon,
                    req.origin.lat,
                    req.equipment_type.strip(),
                    req.origin.lon,
                    req.origin.lat,
                    radius_meters,
                ),
            )
            candidates = cursor.fetchall()

    # If PostGIS query returned candidates, compute H3 cells for each
    results = []
    for c in candidates:
        lat = c["latitude"]
        lon = c["longitude"]
        results.append({
            "hospital_id": str(c["hospital_id"]),
            "hospital_name": c["hospital_name"],
            "available_count": c["available_count"],
            "latitude": lat,
            "longitude": lon,
            "distance_km": round((c["distance_meters"] or 0) / 1000.0, 2),
            "h3_cell": latlng_to_h3(lat, lon, 7) if lat and lon else None,
            "avg_hourly_rate": c["avg_hourly_rate"],
        })

    return {
        "status": "success",
        "equipment_type": req.equipment_type,
        "radius_km": req.radius_km,
        "count": len(results),
        "candidates": results,
    }

@router.post("/routes")
def calculate_road_route(req: RouteCalculationRequest):
    """
    Stage 3 & 4: Road routing via OSRM + traffic congestion classification.
    """
    route_info = gis_client.get_route(
        source={"lat": req.source.lat, "lon": req.source.lon},
        destination={"lat": req.destination.lat, "lon": req.destination.lon},
    )
    return {
        "status": "success",
        "data": route_info,
    }

class NearestSearchRequest(BaseModel):
    equipment_type: str = Field(min_length=1)
    hospital_id: str | None = Field(default=None, description="Requesting hospital UUID (uses its registered coordinates)")
    origin: Coordinate | None = Field(default=None, description="Explicit caller coordinates if not using hospital_id")
    quantity: int = Field(default=1, gt=0)
    max_eta_minutes: int = Field(default=60, gt=0, le=300)

@router.post("/nearest")
def find_nearest_equipment_hospital(req: NearestSearchRequest):
    """
    Finds the nearest verified hospital with available equipment.
    Queries Supabase PostgreSQL directly, performs PostGIS + H3 candidate pruning,
    OSRM road routing, and real-time traffic masking.
    """
    from app.services.dispatch_service import dispatch_logic

    # 1. Resolve origin coordinates from hospital_id if origin is not explicitly given
    origin_lat = None
    origin_lon = None

    if req.origin:
        origin_lat = req.origin.lat
        origin_lon = req.origin.lon
    elif req.hospital_id:
        with get_supabase_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        COALESCE(AVG(ST_Y(ea.location)), AVG(mock.latitude))::float8 AS latitude,
                        COALESCE(AVG(ST_X(ea.location)), AVG(mock.longitude))::float8 AS longitude
                    FROM public.hospitals h
                    LEFT JOIN public.abdm_mock_hfr mock ON h.mvp_hfr_id = mock.mvp_hfr_id
                    LEFT JOIN public.equipment_assets ea ON h.hospital_id = ea.hospital_id
                    WHERE h.hospital_id = %s
                    GROUP BY h.hospital_id
                    """,
                    (req.hospital_id.strip(),),
                )
                h_row = cursor.fetchone()
                if h_row and h_row["latitude"] is not None and h_row["longitude"] is not None:
                    origin_lat = h_row["latitude"]
                    origin_lon = h_row["longitude"]

    if origin_lat is None or origin_lon is None:
        return {
            "status": "ERROR",
            "message": "Origin coordinates could not be resolved. Please provide valid coordinates or hospital_id.",
        }

    proposal = dispatch_logic({
        "equipment_type": req.equipment_type,
        "quantity": req.quantity,
        "location": {"lat": origin_lat, "lon": origin_lon},
        "max_eta_minutes": req.max_eta_minutes,
        "from_hospital_id": req.hospital_id,
        "skip_blockchain": True,
    })

    return {
        "status": "success",
        "data": proposal,
    }

@router.get("/map-config")
def get_map_config():
    """
    Returns standard MapLibre GL JS configuration styles for 3D buildings,
    satellite imagery, and vector street layers.
    """
    return {
        "status": "success",
        "default_center": [88.3639, 22.5726],
        "default_zoom": 13.5,
        "default_pitch": 55,
        "default_bearing": -15,
        "styles": {
            "satellite_3d": {
                "name": "Esri Satellite Imagery 3D",
                "version": 8,
                "sources": {
                    "esri-satellite": {
                        "type": "raster",
                        "tiles": [
                            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        ],
                        "tileSize": 256,
                        "attribution": "Esri World Imagery",
                    }
                },
                "layers": [
                    {"id": "satellite-base", "type": "raster", "source": "esri-satellite"}
                ],
            },
            "vector_street": {
                "name": "OpenFreeMap Liberty Vector",
                "style_url": "https://tiles.openfreemap.org/styles/liberty",
            },
            "dark_matter": {
                "name": "CARTO Dark Matter Tactical",
                "style_url": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            },
            "positron_light": {
                "name": "CARTO Positron Clean",
                "style_url": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            },
        },
        "traffic_palette": {
            "NORMAL": {"color": "#10B981", "glow": "rgba(16, 185, 129, 0.4)", "label": "Smooth Flow"},
            "SLOW": {"color": "#F59E0B", "glow": "rgba(245, 158, 11, 0.4)", "label": "Moderate Rush"},
            "HEAVY": {"color": "#EF4444", "glow": "rgba(239, 68, 68, 0.4)", "label": "Heavy Congestion"},
        },
    }

@router.get("/h3-footprint")
def get_h3_footprint(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    k_rings: int = Query(default=2, ge=1, le=5),
    resolution: int = Query(default=7, ge=5, le=10),
):
    """
    Returns H3 hexagonal coverage polygons in GeoJSON format around given coordinate.
    """
    footprint = gis_client.get_h3_footprint(lat=lat, lon=lon, k_rings=k_rings, resolution=resolution)
    return {
        "status": "success",
        "data": footprint,
    }



