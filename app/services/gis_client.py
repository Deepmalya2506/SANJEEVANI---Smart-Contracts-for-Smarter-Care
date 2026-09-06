from uuid import UUID
import requests

from app.core.config import settings


def get_best_option(origin: dict, hospitals: list[dict], max_eta_minutes: int = 60) -> dict:
    """Dispatches origin coordinates and candidate hospitals to the GIS routing service."""
    # Serialize UUIDs and clean payload
    sanitized_hospitals = []
    for h in hospitals:
        sanitized_hospitals.append({
            "hospital_id": str(h["hospital_id"]) if isinstance(h["hospital_id"], UUID) else h["hospital_id"],
            "hospital_name": h.get("hospital_name", ""),
            "latitude": float(h["latitude"]),
            "longitude": float(h["longitude"]),
            "available_count": int(h.get("available_count", 1)),
        })

    payload = {
        "origin": {
            "lat": float(origin["lat"]),
            "lon": float(origin["lon"]),
        },
        "hospitals": sanitized_hospitals,
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