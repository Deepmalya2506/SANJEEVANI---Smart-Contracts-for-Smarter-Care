from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from GIS_engine.services.osrm_service import get_route

router = APIRouter()

class Coordinate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)

class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: Coordinate
    destination: Coordinate

@router.post("/route")
def get_route_api(request: RouteRequest):
    """
    Direct Point-to-Point OSRM Road Routing:
    Computes turn-by-turn road LineString geometry, road distance (km), and driving duration (mins).
    """
    source = (request.source.lon, request.source.lat)
    destination = (request.destination.lon, request.destination.lat)

    route_data = get_route(source, destination)

    return {
        "status": "SUCCESS",
        "distance_km": round(route_data["distance"] / 1000.0, 2),
        "duration_minutes": round(route_data["duration"] / 60.0, 1),
        "geometry": route_data["geometry"],
        "provider": route_data.get("provider", "osrm"),
    }