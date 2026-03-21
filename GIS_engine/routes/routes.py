from fastapi import APIRouter
from schemas.schema import RouteRequest
from services.osrm_service import get_route
from services.visualization_service import create_route_map

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

@router.post("/route-map")
def route_map_api(request: RouteRequest):
    source = (request.source.lon, request.source.lat)
    destination = (request.destination.lon, request.destination.lat)

    result = get_route(source, destination)

    map_obj = create_route_map(result["geometry"])

    file_path = "route_map.html"
    map_obj.save(file_path)

    return {
        "status": "success",
        "map_file": file_path
    }