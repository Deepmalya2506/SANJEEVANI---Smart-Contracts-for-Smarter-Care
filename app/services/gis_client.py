import requests
from app.core.config import settings

def get_best_option(origin, hospitals):
    response = requests.post(
        f"{settings.GIS_URL}/gis/best-option",
        json={
            "origin": origin,
            "hospitals": hospitals
        }
    )
    try:
        return response.json()
    except Exception:
        return {"error": "Invalid GIS response", "raw": response.text}