from uuid import UUID
import requests

from app.core.config import settings


def get_best_option(origin: dict, hospitals: list[dict], max_eta_minutes: int = 60) -> dict:
    """Dispatches origin coordinates and candidate hospitals to the GIS routing service."""
    sanitized_hospitals = []
    for h in hospitals:
        hid = str(h.get("id") or h.get("hospital_id") or "")
        lat = float(h.get("lat") if h.get("lat") is not None else h.get("latitude", 0.0))
        lon = float(h.get("lon") if h.get("lon") is not None else h.get("longitude", 0.0))
        sanitized_hospitals.append({
            "id": hid,
            "lat": lat,
            "lon": lon,
            "hospital_id": hid,
            "hospital_name": h.get("hospital_name", ""),
            "available_count": int(h.get("available_count", 1)),
        })

    payload = {
        "origin": {
            "lat": float(origin.get("lat", origin.get("latitude", 22.5726))),
            "lon": float(origin.get("lon", origin.get("longitude", 88.3639))),
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