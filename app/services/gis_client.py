from typing import Any
from uuid import UUID
import requests

from app.core.config import settings

def _serialize_candidates(hospitals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized = []
    for h in hospitals:
        sanitized.append({
            "hospital_id": str(h.get("hospital_id") or h.get("id")),
            "hospital_name": h.get("hospital_name", ""),
            "latitude": float(h.get("latitude") if h.get("latitude") is not None else h.get("lat")),
            "longitude": float(h.get("longitude") if h.get("longitude") is not None else h.get("lon")),
            "available_count": int(h.get("available_count") or h.get("available_units", 1)),
            "avg_hourly_rate": float(h.get("avg_hourly_rate") or h.get("hourly_rate", 0.0) or 0.0),
        })
    return sanitized

def get_best_option(origin: dict[str, float], hospitals: list[dict[str, Any]], max_eta_minutes: int = 60) -> dict[str, Any]:
    """Sends origin coordinates and candidate hospitals to the GIS routing service."""
    payload = {
        "origin": {
            "lat": float(origin["lat"]),
            "lon": float(origin["lon"]),
        },
        "hospitals": _serialize_candidates(hospitals),
        "max_eta_minutes": max_eta_minutes,
    }

    url = f"{settings.GIS_URL.rstrip('/')}/gis/best-option"
    try:
        response = requests.post(url, json=payload, timeout=12)
        if response.status_code >= 400:
            return {
                "error": f"GIS service returned HTTP {response.status_code}",
                "detail": response.text,
            }
        return response.json()
    except requests.Timeout:
        return {"error": "GIS route calculation timed out."}
    except requests.RequestException as exc:
        return {"error": f"Unable to reach GIS service: {exc}"}

def get_route(source: dict[str, float], destination: dict[str, float]) -> dict[str, Any]:
    """Fetches OSRM driving route and traffic classification."""
    payload = {
        "source": {"lat": float(source["lat"]), "lon": float(source["lon"])},
        "destination": {"lat": float(destination["lat"]), "lon": float(destination["lon"])},
    }
    url = f"{settings.GIS_URL.rstrip('/')}/gis/route"
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", {})
        return {"error": f"Route request failed: HTTP {response.status_code}"}
    except Exception as exc:
        return {"error": f"Unable to reach GIS service: {exc}"}

def evaluate_feasibility(
    origin: dict[str, float],
    candidates: list[dict[str, Any]],
    max_eta_minutes: int = 60,
    h3_resolution: int = 7,
    traffic_mode: str | None = None,
) -> dict[str, Any]:
    """Evaluates multi-candidate feasibility through the 5-stage GIS engine."""
    payload = {
        "origin": {
            "lat": float(origin["lat"]),
            "lon": float(origin["lon"]),
        },
        "candidates": _serialize_candidates(candidates),
        "max_eta_minutes": max_eta_minutes,
        "h3_resolution": h3_resolution,
        "traffic_mode": traffic_mode,
    }
    url = f"{settings.GIS_URL.rstrip('/')}/gis/feasibility"
    try:
        response = requests.post(url, json=payload, timeout=12)
        if response.status_code >= 400:
            return {
                "error": f"GIS service returned HTTP {response.status_code}",
                "detail": response.text,
            }
        return response.json()
    except requests.Timeout:
        return {"error": "GIS feasibility calculation timed out."}
    except requests.RequestException as exc:
        return {"error": f"Unable to reach GIS service: {exc}"}

def get_h3_footprint(lat: float, lon: float, k_rings: int = 2, resolution: int = 7) -> dict[str, Any]:
    """Generates H3 coverage footprint GeoJSON."""
    payload = {
        "center": {"lat": lat, "lon": lon},
        "k_rings": k_rings,
        "resolution": resolution,
    }
    url = f"{settings.GIS_URL.rstrip('/')}/gis/h3-footprint"
    try:
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code == 200:
            return response.json().get("data", {})
        return {"error": f"H3 footprint request failed: HTTP {response.status_code}"}
    except Exception as exc:
        return {"error": f"Unable to reach GIS service: {exc}"}