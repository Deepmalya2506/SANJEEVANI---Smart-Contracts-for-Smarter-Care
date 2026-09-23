from datetime import datetime, timezone, timedelta
from typing import Any

# Congestion levels and penalties
TRAFFIC_NORMAL = "NORMAL"
TRAFFIC_SLOW = "SLOW"
TRAFFIC_HEAVY = "HEAVY"
TRAFFIC_UNKNOWN = "UNKNOWN"

PENALTY_MULTIPLIERS = {
    TRAFFIC_NORMAL: 1.0,
    TRAFFIC_SLOW: 1.25,
    TRAFFIC_HEAVY: 1.6,
    TRAFFIC_UNKNOWN: 1.0,
}

TRAFFIC_COLORS = {
    TRAFFIC_NORMAL: "#10B981",  # Emerald Green
    TRAFFIC_SLOW: "#F59E0B",    # Amber
    TRAFFIC_HEAVY: "#EF4444",   # Red
    TRAFFIC_UNKNOWN: "#64748B", # Slate
}

# IST Timezone (UTC +5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_current_ist_time() -> datetime:
    return datetime.now(IST)

def determine_congestion_level(
    origin: tuple[float, float],
    destination: tuple[float, float],
    distance_meters: float,
    current_time: datetime | None = None,
) -> str:
    """
    Pluggable traffic heuristic evaluating corridor congestion based on:
    1. Time of day in India (Peak morning: 08:30-11:30, Peak evening: 17:00-20:30)
    2. Corridor length / urban density penalty
    """
    if current_time is None:
        current_time = get_current_ist_time()

    hour = current_time.hour
    minute = current_time.minute
    total_minutes = hour * 60 + minute

    # Peak rush hour ranges in minutes from midnight IST
    morning_peak_start = 8 * 60 + 30   # 08:30
    morning_peak_end = 11 * 60 + 30    # 11:30
    evening_peak_start = 17 * 60       # 17:00
    evening_peak_end = 20 * 60 + 30    # 20:30

    is_morning_peak = morning_peak_start <= total_minutes <= morning_peak_end
    is_evening_peak = evening_peak_start <= total_minutes <= evening_peak_end
    is_night = total_minutes < 6 * 60 or total_minutes > 22 * 60

    if is_morning_peak or is_evening_peak:
        # If long corridor in peak hours, heavy congestion
        if distance_meters > 8000:
            return TRAFFIC_HEAVY
        return TRAFFIC_SLOW

    if is_night:
        return TRAFFIC_NORMAL

    # Normal daytime hours
    if distance_meters > 15000:
        return TRAFFIC_SLOW
    return TRAFFIC_NORMAL

def apply_traffic_mask(
    origin: tuple[float, float],
    destination: tuple[float, float],
    distance_meters: float,
    baseline_duration_seconds: float,
    traffic_status_override: str | None = None,
) -> dict[str, Any]:
    """
    Applies the traffic mask to a baseline OSRM route.
    Returns the congestion status, penalty multiplier, adjusted duration, and color representation.
    """
    status = (
        traffic_status_override
        if traffic_status_override in PENALTY_MULTIPLIERS
        else determine_congestion_level(origin, destination, distance_meters)
    )

    multiplier = PENALTY_MULTIPLIERS.get(status, 1.0)
    adjusted_seconds = baseline_duration_seconds * multiplier
    adjusted_eta_min = round(adjusted_seconds / 60.0, 1)

    return {
        "traffic_status": status,
        "penalty_multiplier": multiplier,
        "baseline_eta_min": round(baseline_duration_seconds / 60.0, 1),
        "traffic_adjusted_eta_min": adjusted_eta_min,
        "adjusted_duration_seconds": round(adjusted_seconds, 1),
        "traffic_color": TRAFFIC_COLORS.get(status, "#10B981"),
    }

def colorize_route_segments(
    geometry: dict[str, Any],
    traffic_status: str,
) -> list[dict[str, Any]]:
    """
    Produces segmented GeoJSON Features with traffic severity colors for MapLibre multi-color polyline rendering.
    """
    coordinates = geometry.get("coordinates", [])
    if not coordinates:
        return []

    color = TRAFFIC_COLORS.get(traffic_status, "#10B981")
    return [
        {
            "type": "Feature",
            "properties": {
                "traffic_status": traffic_status,
                "color": color,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates,
            },
        }
    ]
