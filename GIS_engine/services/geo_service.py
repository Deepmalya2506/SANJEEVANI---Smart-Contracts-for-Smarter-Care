from typing import Any
from GIS_engine.services.h3_service import prune_redundant_candidates, latlng_to_h3, get_h3_coverage_geojson
from GIS_engine.services.osrm_service import get_distance_matrix, get_route
from GIS_engine.services.traffic_service import apply_traffic_mask, colorize_route_segments

def evaluate_gis_feasibility(
    origin: tuple[float, float],  # (lon, lat)
    candidates: list[Any],
    max_eta_minutes: int = 60,
    h3_resolution: int = 7,
    traffic_mode: str | None = None,
) -> dict[str, Any]:
    """
    Executes Stages 2, 3, and 4 of the GIS pipeline:
    - Stage 2: Uber H3 Hex Pruning
    - Stage 3: OSRM Road Routing
    - Stage 4: Traffic Mask Heuristic & Feasibility Evaluation
    """
    if not candidates:
        return {
            "status": "NO_CANDIDATES",
            "message": "No candidate facilities provided.",
            "candidates": [],
        }

    # Normalize Pydantic models to dicts
    candidates_dict = [
        c.model_dump() if hasattr(c, "model_dump") else (dict(c) if isinstance(c, dict) else c.__dict__)
        for c in candidates
    ]

    origin_lon, origin_lat = origin
    origin_h3 = latlng_to_h3(origin_lat, origin_lon, resolution=h3_resolution)

    # Stage 2: H3 Hex Pruning
    pruned_candidates = prune_redundant_candidates(candidates_dict, resolution=h3_resolution, max_per_cell=2)

    # Build coordinate list for distance matrix: [origin, candidate_1, candidate_2, ...]
    coords = [(origin_lon, origin_lat)] + [
        (
            float(c.get("lon") if c.get("lon") is not None else c.get("longitude")),
            float(c.get("lat") if c.get("lat") is not None else c.get("latitude")),
        )
        for c in pruned_candidates
    ]

    # Stage 3: OSRM Road Matrix
    matrix = get_distance_matrix(coords)
    durations = matrix["durations"][0]   # origin -> each candidate
    distances = matrix["distances"][0]

    evaluated_options = []

    for i, candidate in enumerate(pruned_candidates):
        dest_lon = float(candidate.get("lon") if candidate.get("lon") is not None else candidate.get("longitude"))
        dest_lat = float(candidate.get("lat") if candidate.get("lat") is not None else candidate.get("latitude"))
        hospital_id = str(candidate.get("hospital_id") or candidate.get("id"))

        raw_dist = distances[i + 1] if (i + 1 < len(distances) and distances[i + 1] is not None) else 999999
        raw_dur = durations[i + 1] if (i + 1 < len(durations) and durations[i + 1] is not None) else 999999

        # Stage 4: Traffic Mask Adjustment
        traffic_info = apply_traffic_mask(
            origin=(origin_lat, origin_lon),
            destination=(dest_lat, dest_lon),
            distance_meters=raw_dist,
            baseline_duration_seconds=raw_dur,
            traffic_status_override=traffic_mode,
        )

        adjusted_eta = traffic_info["traffic_adjusted_eta_min"]
        is_feasible = adjusted_eta <= max_eta_minutes
        dist_km = round(raw_dist / 1000.0, 2)

        evaluated_options.append({
            "hospital_id": hospital_id,
            "hospital_name": candidate.get("hospital_name", ""),
            "h3_cell": candidate.get("h3_cell") or latlng_to_h3(dest_lat, dest_lon, h3_resolution),
            "coordinates": {"lat": dest_lat, "lon": dest_lon},
            "distance_km": dist_km,
            "distance_m": raw_dist,
            "baseline_eta_min": traffic_info["baseline_eta_min"],
            "traffic_adjusted_eta_min": adjusted_eta,
            "traffic_status": traffic_info["traffic_status"],
            "traffic_color": traffic_info["traffic_color"],
            "penalty_multiplier": traffic_info["penalty_multiplier"],
            "feasible": is_feasible,
            "available_count": int(candidate.get("available_count") or candidate.get("available_units", 1)),
            "avg_hourly_rate": float(candidate.get("avg_hourly_rate") or candidate.get("hourly_rate", 0) or 0),
        })

    # Sort candidates by:
    # 1. Feasibility (feasible first)
    # 2. Traffic-adjusted ETA
    # 3. Available units (higher preferred)
    evaluated_options.sort(
        key=lambda x: (
            0 if x["feasible"] else 1,
            x["traffic_adjusted_eta_min"],
            -x["available_count"],
        )
    )

    best_candidate = evaluated_options[0] if evaluated_options else None
    best_route_geometry = None
    best_route_segments = []

    if best_candidate:
        # Fetch detailed turn-by-turn road geometry for the winning candidate
        dest_coords = (best_candidate["coordinates"]["lon"], best_candidate["coordinates"]["lat"])
        route_res = get_route(origin, dest_coords)
        best_route_geometry = route_res.get("geometry")
        if best_route_geometry:
            best_route_segments = colorize_route_segments(
                best_route_geometry,
                best_candidate.get("traffic_status", "NORMAL"),
            )

    return {
        "status": "SUCCESS",
        "origin": {"lat": origin_lat, "lon": origin_lon, "h3_cell": origin_h3},
        "max_eta_minutes": max_eta_minutes,
        "best_hospital": best_candidate["hospital_id"] if best_candidate else None,
        "best_option": {
            **best_candidate,
            "route_geometry": best_route_geometry,
            "route_segments": best_route_segments,
        } if best_candidate else None,
        "all_options": evaluated_options,
        "h3_coverage": get_h3_coverage_geojson(origin_lat, origin_lon, k_rings=2, resolution=h3_resolution),
    }

def find_best_option(origin: tuple[float, float], hospitals: list[dict[str, Any]]) -> dict[str, Any]:
    """Compatibility adapter for MCP server and existing caller endpoints."""
    return evaluate_gis_feasibility(origin=origin, candidates=hospitals)

def find_nearest(user_location: tuple[float, float], hospitals: list[Any]) -> dict[str, Any]:
    """Compatibility adapter for /gis/nearest endpoint."""
    candidates = [
        {
            "hospital_id": getattr(h, "id", None) or h.get("id") or h.get("hospital_id"),
            "lat": getattr(h, "lat", None) or h.get("lat") or h.get("latitude"),
            "lon": getattr(h, "lon", None) or h.get("lon") or h.get("longitude"),
        }
        for h in hospitals
    ]
    res = evaluate_gis_feasibility(origin=user_location, candidates=candidates)
    best = res.get("best_option") or {}
    return {
        "nearest": res.get("best_hospital"),
        "distance_km": best.get("distance_km", 0),
        "eta_min": best.get("traffic_adjusted_eta_min", 0),
        "all_options": res.get("all_options", []),
    }