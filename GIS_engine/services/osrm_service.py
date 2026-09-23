import math
import requests
from GIS_engine.config import OSRM_BASE_URL, OSRM_ROUTE_URL

def calculate_haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Fallback distance calculation in meters between two coordinates."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def get_distance_matrix(coordinates: list[tuple[float, float]]) -> dict:
    """
    coordinates: list of (lon, lat)
    Calls OSRM /table/v1/driving API. If OSRM is unreachable, falls back to geodesic estimation.
    """
    coords_str = ";".join([f"{lon:.6f},{lat:.6f}" for lon, lat in coordinates])
    url = f"{OSRM_BASE_URL}/table/v1/driving/{coords_str}?annotations=distance,duration"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "distances" in data and "durations" in data:
                return {
                    "distances": data["distances"],
                    "durations": data["durations"],
                    "source": "osrm",
                }
    except Exception:
        pass

    # Fallback to estimated geodesic road distance (assuming 35 km/h urban average speed)
    n = len(coordinates)
    distances = [[0.0] * n for _ in range(n)]
    durations = [[0.0] * n for _ in range(n)]
    avg_speed_mps = 35.0 * 1000.0 / 3600.0  # ~9.72 m/s

    for i in range(n):
        for j in range(n):
            if i != j:
                dist = calculate_haversine_distance(
                    coordinates[i][0], coordinates[i][1],
                    coordinates[j][0], coordinates[j][1],
                ) * 1.3  # 1.3 road curvature winding factor
                distances[i][j] = dist
                durations[i][j] = dist / avg_speed_mps

    return {
        "distances": distances,
        "durations": durations,
        "source": "fallback_geodesic",
    }

def get_route(source: tuple[float, float], destination: tuple[float, float]) -> dict:
    """
    source, destination = (lon, lat)
    Returns: GeoJSON LineString geometry, distance in meters, duration in seconds.
    """
    coord_string = f"{source[0]:.6f},{source[1]:.6f};{destination[0]:.6f},{destination[1]:.6f}"
    url = f"{OSRM_ROUTE_URL}{coord_string}?overview=full&geometries=geojson&steps=true"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("routes"):
                route = data["routes"][0]
                return {
                    "geometry": route["geometry"],
                    "distance": float(route["distance"]),
                    "duration": float(route["duration"]),
                    "provider": "osrm",
                }
    except Exception:
        pass

    # Fallback straight line polyline if OSRM engine endpoint fails
    dist = calculate_haversine_distance(source[0], source[1], destination[0], destination[1]) * 1.3
    dur = dist / (35.0 * 1000.0 / 3600.0)
    return {
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [source[0], source[1]],
                [destination[0], destination[1]],
            ],
        },
        "distance": dist,
        "duration": dur,
        "provider": "fallback_straight_line",
    }