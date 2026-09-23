import h3
from typing import Any, List, Optional
from fastapi import APIRouter, Query, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from psycopg.rows import dict_row

from GIS_engine.services.h3_service import latlng_to_h3, h3_to_geojson_polygon, h3_to_latlng
from GIS_engine.services.osrm_service import get_route, calculate_haversine_distance
from GIS_engine.services.visualization_service import generate_route_map_html, save_route_map_file

router = APIRouter()

# ── Schemas ──────────────────────────────────────────────────────────────────

class SourceFacility(BaseModel):
    model_config = ConfigDict(extra="ignore")
    hospital_id: Optional[str] = None
    hospital_name: Optional[str] = None
    mvp_hfr_id: Optional[str] = None
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)

class HospitalCandidate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    mvp_hfr_id: Optional[str] = None
    lat: float
    lon: float
    network_status: str = "ABDM_VERIFIED"
    verification_status: str = "VERIFIED"
    address: Optional[str] = None
    h3_cell: Optional[str] = None

class CandidateDiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: SourceFacility
    radius_km: float = Field(default=60.0, gt=0.0, le=500.0)
    limit: int = Field(default=50, ge=5, le=100)

class H3FilterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: SourceFacility
    candidates: List[HospitalCandidate]
    initial_k_ring: int = Field(default=2, ge=1, le=8)
    max_k_ring: int = Field(default=5, ge=2, le=10)
    h3_resolution: int = Field(default=7, ge=5, le=10)

class RoadMatrixRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: SourceFacility
    candidates: List[HospitalCandidate]

class SequentialPipelineRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: SourceFacility
    radius_km: float = Field(default=60.0, gt=0.0, le=500.0)
    initial_k_ring: int = Field(default=2, ge=1, le=8)
    max_k_ring: int = Field(default=5, ge=2, le=10)
    candidate_limit: int = Field(default=50, ge=5, le=100)
    h3_resolution: int = Field(default=7, ge=5, le=10)

def _get_db_connection():
    try:
        from app.core.database import get_supabase_connection
        return get_supabase_connection()
    except Exception:
        return None

# Rank Color Palette (Best 5 Networks)
RANK_COLORS = {
    1: "#10B981",  # Rank 1: Emerald
    2: "#38BDF8",  # Rank 2: Cyan
    3: "#818CF8",  # Rank 3: Indigo
    4: "#F59E0B",  # Rank 4: Amber
    5: "#F43F5E",  # Rank 5: Rose
}
OTHER_REACHABLE_COLOR = "#64748B"  # Muted Slate

# ── STAGE 1: Starting / Entrypoint Candidate Discovery ───────────────────────

@router.post("/candidates")
def discover_candidates_api(request: CandidateDiscoveryRequest):
    """
    STAGE 1 ENTRYPOINT (PostGIS Spatial Proximity):
    Starting entrypoint for MCP and user requests.
    Queries the database and returns the first filtered list of up to 50 authentic
    nearby hospitals in the Region of Interest (ROI) around the source coordinates.
    """
    src = request.source
    src_lat, src_lon = src.latitude, src.longitude
    src_h3 = latlng_to_h3(src_lat, src_lon, 7)

    conn = _get_db_connection()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL database connection unavailable.",
        )

    delta_deg = request.radius_km / 111.0
    min_lat, max_lat = src_lat - delta_deg, src_lat + delta_deg
    min_lon, max_lon = src_lon - delta_deg, src_lon + delta_deg

    hospitals: List[dict] = []
    try:
        with conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # 1. Registered platform facilities within ROI
                cursor.execute(
                    """
                    SELECT 
                        h.hospital_id::text AS id,
                        h.hospital_name AS name,
                        h.mvp_hfr_id,
                        h.verification_status,
                        h.profile_status,
                        COALESCE(AVG(ST_Y(ea.location)), AVG(mock.latitude))::float8 AS lat,
                        COALESCE(AVG(ST_X(ea.location)), AVG(mock.longitude))::float8 AS lon,
                        'REGISTERED' AS network_status,
                        mock.address
                    FROM public.hospitals h
                    LEFT JOIN public.abdm_mock_hfr mock ON h.mvp_hfr_id = mock.mvp_hfr_id
                    LEFT JOIN public.equipment_assets ea ON h.hospital_id = ea.hospital_id
                    WHERE h.profile_status = 'ACTIVE'
                    GROUP BY h.hospital_id, h.hospital_name, h.mvp_hfr_id, h.verification_status, h.profile_status, mock.address
                    HAVING (
                        COALESCE(AVG(ST_Y(ea.location)), AVG(mock.latitude)) BETWEEN %s AND %s
                        AND COALESCE(AVG(ST_X(ea.location)), AVG(mock.longitude)) BETWEEN %s AND %s
                    )
                    """,
                    (min_lat, max_lat, min_lon, max_lon),
                )
                reg_rows = cursor.fetchall()
                for r in reg_rows:
                    if r["lat"] is not None and r["lon"] is not None:
                        hospitals.append({
                            "id": r["id"],
                            "name": r["name"],
                            "mvp_hfr_id": r["mvp_hfr_id"],
                            "lat": float(r["lat"]),
                            "lon": float(r["lon"]),
                            "network_status": r["network_status"],
                            "verification_status": r["verification_status"],
                            "address": r["address"] or "Registered Platform Facility",
                            "h3_cell": latlng_to_h3(float(r["lat"]), float(r["lon"]), 7),
                        })

                # 2. ABDM directory facilities within ROI
                cursor.execute(
                    """
                    SELECT 
                        mock.mvp_hfr_id AS id,
                        mock.hospital_name AS name,
                        mock.mvp_hfr_id,
                        mock.latitude::float8 AS lat,
                        mock.longitude::float8 AS lon,
                        'ABDM_VERIFIED' AS network_status,
                        'VERIFIED' AS verification_status,
                        mock.address
                    FROM public.abdm_mock_hfr mock
                    WHERE mock.latitude IS NOT NULL AND mock.longitude IS NOT NULL
                      AND mock.latitude BETWEEN %s AND %s
                      AND mock.longitude BETWEEN %s AND %s
                    LIMIT %s
                    """,
                    (min_lat, max_lat, min_lon, max_lon, request.limit),
                )
                abdm_rows = cursor.fetchall()
                existing_hfrs = {h.get("mvp_hfr_id") for h in hospitals if h.get("mvp_hfr_id")}

                for r in abdm_rows:
                    if r["mvp_hfr_id"] not in existing_hfrs:
                        hospitals.append({
                            "id": r["id"],
                            "name": r["name"],
                            "mvp_hfr_id": r["mvp_hfr_id"],
                            "lat": float(r["lat"]),
                            "lon": float(r["lon"]),
                            "network_status": r["network_status"],
                            "verification_status": r["verification_status"],
                            "address": r["address"] or "Official ABDM Verified Facility",
                            "h3_cell": latlng_to_h3(float(r["lat"]), float(r["lon"]), 7),
                        })

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(exc)}",
        )

    # Filter out source itself if within 50 meters
    hospitals = [
        h for h in hospitals
        if calculate_haversine_distance(src_lon, src_lat, h["lon"], h["lat"]) > 50
    ][:request.limit]

    if not hospitals:
        return {
            "status": "NO_CANDIDATES_FOUND",
            "message": "No healthcare facilities found within specified radius.",
            "source": {
                "hospital_id": src.hospital_id,
                "hospital_name": src.hospital_name or "Designated Source Hospital",
                "mvp_hfr_id": src.mvp_hfr_id,
                "latitude": src_lat,
                "longitude": src_lon,
                "h3_cell": src_h3,
            },
            "radius_km": request.radius_km,
            "count": 0,
            "candidates": [],
        }

    return {
        "status": "SUCCESS",
        "source": {
            "hospital_id": src.hospital_id,
            "hospital_name": src.hospital_name or "Designated Source Hospital",
            "mvp_hfr_id": src.mvp_hfr_id,
            "latitude": src_lat,
            "longitude": src_lon,
            "h3_cell": src_h3,
        },
        "radius_km": request.radius_km,
        "count": len(hospitals),
        "candidates": hospitals,
    }

# ── STAGE 2: H3 Spatial Clustering & Dynamic Expansion ──────────────────────

@router.post("/h3-filter")
def h3_spatial_filter_api(request: H3FilterRequest):
    """
    STAGE 2: H3 Resolution 7 Spatial Cluster Filtering & Dynamic Expansion.
    Clusters candidate facilities around the source hospital's H3 cell.
    Dynamically expands k-ring radius (k=2 -> 3 -> 4 -> 5) if candidates are sparse.
    """
    src = request.source
    src_lat, src_lon = src.latitude, src.longitude
    src_h3 = latlng_to_h3(src_lat, src_lon, request.h3_resolution)

    current_k = request.initial_k_ring
    clustered = []
    disk_cells = set()

    while current_k <= request.max_k_ring:
        disk_cells = set(h3.grid_disk(src_h3, current_k))
        clustered = [
            c for c in request.candidates
            if (c.h3_cell or latlng_to_h3(c.lat, c.lon, request.h3_resolution)) in disk_cells
        ]
        if len(clustered) >= 3 or current_k == request.max_k_ring:
            break
        current_k += 1

    if not clustered:
        return {
            "status": "NO_HOSPITAL_NEARBY",
            "message": f"No hospital nearby within reachability threshold (expanded to k-ring {request.max_k_ring}).",
            "source": src.model_dump(),
            "expanded_k_ring": current_k,
            "clustered_count": 0,
            "outer_count": len(request.candidates),
            "clustered_candidates": [],
            "outer_candidates": [c.model_dump() for c in request.candidates],
            "h3_cluster_footprint": {"type": "FeatureCollection", "features": []},
        }

    clustered_ids = {c.id for c in clustered}
    outer = [c.model_dump() for c in request.candidates if c.id not in clustered_ids]

    # Generate H3 cluster polygon features
    features = []
    for cell in disk_cells:
        poly = h3_to_geojson_polygon(cell)
        c_lat, c_lon = h3_to_latlng(cell)
        dist = h3.grid_distance(src_h3, cell)
        features.append({
            "type": "Feature",
            "properties": {
                "h3_index": cell,
                "ring": dist,
                "is_center": (cell == src_h3),
                "center": {"lat": c_lat, "lon": c_lon},
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly],
            }
        })

    return {
        "status": "SUCCESS",
        "source": {**src.model_dump(), "h3_cell": src_h3},
        "expanded_k_ring": current_k,
        "clustered_count": len(clustered),
        "outer_count": len(outer),
        "clustered_candidates": [c.model_dump() for c in clustered],
        "outer_candidates": outer,
        "h3_cluster_footprint": {
            "type": "FeatureCollection",
            "features": features,
        }
    }

# ── STAGE 3: Road Distance & Duration Matrix ────────────────────────────────

@router.post("/matrix")
def compute_road_matrix_api(request: RoadMatrixRequest):
    """
    STAGE 3: OSRM Turn-by-Turn Road Distance & Baseline Duration Matrix.
    Computes true road network paths and travel times from source to each candidate.
    """
    src = request.source
    src_coords = (src.longitude, src.latitude)
    src_h3 = latlng_to_h3(src.latitude, src.longitude, 7)

    matrix_results = []
    for cand in request.candidates:
        dest_coords = (cand.lon, cand.lat)
        route_res = get_route(src_coords, dest_coords)
        cand_h3 = cand.h3_cell or latlng_to_h3(cand.lat, cand.lon, 7)
        h3_dist = h3.grid_distance(src_h3, cand_h3)

        matrix_results.append({
            "hospital_id": cand.id,
            "hospital_name": cand.name,
            "mvp_hfr_id": cand.mvp_hfr_id,
            "address": cand.address,
            "network_status": cand.network_status,
            "coordinates": {"lat": cand.lat, "lon": cand.lon},
            "h3_cell": cand_h3,
            "h3_grid_distance": h3_dist,
            "distance_km": round(route_res["distance"] / 1000.0, 2),
            "duration_minutes": round(route_res["duration"] / 60.0, 1),
            "route_geometry": route_res["geometry"],
            "provider": route_res.get("provider", "osrm"),
        })

    # Sort by duration ascending
    matrix_results.sort(key=lambda x: (x["duration_minutes"], x["distance_km"]))

    return {
        "status": "SUCCESS",
        "source": {**src.model_dump(), "h3_cell": src_h3},
        "count": len(matrix_results),
        "matrix": matrix_results,
    }

# ── STAGE 4: Penultimate Cascading Sequential Pipeline Endpoint ──────────────

@router.post("/pathways")
def compute_cascading_pipeline_api(request: SequentialPipelineRequest):
    """
    STAGE 4 PENULTIMATE CASCADING ENDPOINT:
    Connects the entire sequential workflow in one connected call:
    Stage 1: PostGIS Discovery (max 50 ROI facilities)
      ↓
    Stage 2: Uber H3 Resolution 7 Clustering & Dynamic Expansion
      ↓
    Stage 3: OSRM Turn-by-Turn Road Matrix & 95% Opacity Polylines
      ↓
    Stage 4: Best 5 Networks Ranking & Legend Assignment
    """
    # 1. Stage 1: Candidate Discovery
    disc_res = discover_candidates_api(
        CandidateDiscoveryRequest(
            source=request.source,
            radius_km=request.radius_km,
            limit=request.candidate_limit,
        )
    )
    if disc_res["status"] != "SUCCESS":
        return disc_res

    candidates_raw = disc_res["candidates"]
    candidates = [HospitalCandidate(**c) for c in candidates_raw]

    # 2. Stage 2: H3 Spatial Filter & Dynamic Expansion
    h3_res = h3_spatial_filter_api(
        H3FilterRequest(
            source=request.source,
            candidates=candidates,
            initial_k_ring=request.initial_k_ring,
            max_k_ring=request.max_k_ring,
            h3_resolution=request.h3_resolution,
        )
    )
    if h3_res["status"] != "SUCCESS":
        return h3_res

    clustered_candidates = [HospitalCandidate(**c) for c in h3_res["clustered_candidates"]]
    outer_candidates = [HospitalCandidate(**c) for c in h3_res["outer_candidates"]]

    # 3. Stage 3: Road Matrix for all candidates
    all_cand_objs = clustered_candidates + outer_candidates
    matrix_res = compute_road_matrix_api(
        RoadMatrixRequest(
            source=request.source,
            candidates=all_cand_objs,
        )
    )
    pathways = matrix_res["matrix"]

    clustered_id_set = {c.id for c in clustered_candidates}
    for p in pathways:
        p["in_h3_cluster"] = p["hospital_id"] in clustered_id_set

    # Sort pathways: Clustered first, then by duration / distance
    pathways.sort(
        key=lambda x: (
            0 if x["in_h3_cluster"] else 1,
            x["duration_minutes"],
            x["distance_km"],
        )
    )

    # 4. Stage 4: Assign Ranks & Colors (Best 5 Networks)
    for idx, item in enumerate(pathways):
        rank = idx + 1
        item["rank"] = rank
        if rank <= 5 and item["in_h3_cluster"]:
            item["color"] = RANK_COLORS.get(rank, OTHER_REACHABLE_COLOR)
            item["is_best_5"] = True
        else:
            item["color"] = OTHER_REACHABLE_COLOR
            item["is_best_5"] = False

    best_5 = [p for p in pathways if p["is_best_5"]][:5]

    result_data = {
        "status": "SUCCESS",
        "source": disc_res["source"],
        "stage_1_postgis": {
            "radius_km": request.radius_km,
            "total_candidates_found": len(candidates_raw),
        },
        "stage_2_h3_cluster": {
            "resolution": request.h3_resolution,
            "expanded_k_ring": h3_res["expanded_k_ring"],
            "clustered_count": h3_res["clustered_count"],
            "outer_count": h3_res["outer_count"],
            "h3_cluster_footprint": h3_res["h3_cluster_footprint"],
        },
        "stage_3_road_matrix": {
            "total_pathways_computed": len(pathways),
            "best_5_networks": best_5,
            "all_pathways": pathways,
        },
        "rank_legend": [
            {"rank": 1, "label": "Rank #1 Primary Corridor", "color": "#10B981"},
            {"rank": 2, "label": "Rank #2 Secondary Corridor", "color": "#38BDF8"},
            {"rank": 3, "label": "Rank #3 Tertiary Corridor", "color": "#818CF8"},
            {"rank": 4, "label": "Rank #4 Alternate Corridor", "color": "#F59E0B"},
            {"rank": 5, "label": "Rank #5 Auxiliary Corridor", "color": "#F43F5E"},
            {"rank": 6, "label": "Outer Facilities (Non-Clustered)", "color": "#64748B"},
        ],
        "map_url": "/route-map",
        "route_map_updated": True,
    }

    try:
        save_route_map_file(result_data)
    except Exception as exc:
        print(f"Notice: Failed to auto-save route_map.html: {exc}")

    return result_data

# ── STAGE 5 / FINAL: Dynamic Route Map Generator Endpoint ───────────────────

@router.post("/route-map")
def generate_dynamic_route_map_api(request: SequentialPipelineRequest, raw_html: bool = Query(default=False)):
    """
    STAGE 5 DYNAMIC MAP GENERATOR ENDPOINT:
    Takes any source facility, runs the sequential pipeline, generates and saves
    the updated dynamic route_map.html on disk, and returns the live route-map view.
    """
    pipeline_res = compute_cascading_pipeline_api(request)
    if pipeline_res.get("status") != "SUCCESS":
        return pipeline_res

    html_content = generate_route_map_html(pipeline_res)
    save_route_map_file(pipeline_res)

    if raw_html:
        return HTMLResponse(content=html_content)

    return {
        "status": "SUCCESS",
        "message": "Route map successfully generated and updated with authentic dynamic data.",
        "map_url": f"/route-map?lat={request.source.latitude}&lon={request.source.longitude}&name={request.source.hospital_name or 'Source'}&hfr={request.source.mvp_hfr_id or ''}",
        "file_updated": "GIS_engine/route_map.html",
        "pipeline": pipeline_res,
    }

# ── Helper: Adjoint H3 Hexagon Neighbors ─────────────────────────────────────

@router.get("/tiles/neighbors")
def get_h3_neighbors_api(
    h3_index: Optional[str] = Query(default=None),
    lat: Optional[float] = Query(default=None),
    lon: Optional[float] = Query(default=None),
    k_rings: int = Query(default=2, ge=1, le=6),
    resolution: int = Query(default=7, ge=5, le=10),
):
    """
    Returns GeoJSON FeatureCollection of adjoint neighbouring H3 hex cells up to k_rings
    around the specified H3 index or (lat, lon) coordinates.
    """
    if not h3_index:
        if lat is None or lon is None:
            raise HTTPException(status_code=400, detail="Provide either h3_index or lat and lon")
        h3_index = latlng_to_h3(lat, lon, resolution)

    try:
        center_cell = h3_index
        cells = h3.grid_disk(center_cell, k_rings)
        features = []
        for cell in cells:
            dist = h3.grid_distance(center_cell, cell)
            poly = h3_to_geojson_polygon(cell)
            c_lat, c_lon = h3_to_latlng(cell)
            features.append({
                "type": "Feature",
                "properties": {
                    "h3_index": cell,
                    "ring": dist,
                    "is_center": (cell == center_cell),
                    "center": {"lat": c_lat, "lon": c_lon},
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [poly],
                },
            })

        return {
            "status": "SUCCESS",
            "center_h3": center_cell,
            "k_rings": k_rings,
            "count": len(features),
            "data": {
                "type": "FeatureCollection",
                "features": features,
            }
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
