from fastapi import APIRouter
from schemas.schema import RouteRequest, IsochroneRequest, BestOptionRequest
from services.osrm_service import get_route
from services.visualization_service import create_route_map
from services.isochrone_service import generate_circle, time_to_radius_km
from services.geo_service import find_best_option

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

@router.post("/isochrone")
def isochrone_api(request: IsochroneRequest):
    lat = request.center.lat
    lon = request.center.lon

    radius_km = time_to_radius_km(request.time_minutes)

    polygon = generate_circle(lat, lon, radius_km)

    return {
        "status": "success",
        "data": {
            "radius_km": radius_km,
            "isochrone": polygon
        }
    }

@router.post("/isochrone-map")
def isochrone_map_api(request: IsochroneRequest):
    radius_km = time_to_radius_km(request.time_minutes)

    polygon = generate_circle(
        request.center.lat,
        request.center.lon,
        radius_km
    )

    from services.visualization_service import create_isochrone_map

    m = create_isochrone_map(
        request.center.dict(),
        polygon
    )

    file_path = "isochrone_map.html"
    m.save(file_path)

    return {
        "status": "success",
        "map_file": file_path
    }

@router.post("/best-option")
def best_option_api(request: BestOptionRequest):

    origin = (request.origin.lon, request.origin.lat)

    hospitals = [
        {
            "id": h.id,
            "lat": h.lat,
            "lon": h.lon
        }
        for h in request.hospitals
    ]

    result = find_best_option(origin, hospitals)

    return {
        "status": "success",
        "data": result
    }