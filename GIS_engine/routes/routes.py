from fastapi import APIRouter
from schemas.schema import RouteRequest
from services.osrm_service import get_route

router = APIRouter()

@router.post("/route")
def get_route_api(request: RouteRequest):
    source = (request.source.lon, request.source.lat)
    destination = (request.destination.lon, request.destination.lat)

    result = get_route(source, destination)

    return {
        "status": "success",
        "data": result
    }