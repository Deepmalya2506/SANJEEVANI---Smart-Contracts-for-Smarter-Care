from fastapi import APIRouter
from GIS_engine.schemas.schema import NearestRequest
from GIS_engine.services.geo_service import find_nearest

router = APIRouter()

@router.post("/nearest")
def get_nearest(request: NearestRequest):
    user = (request.user_location.lon, request.user_location.lat)

    result = find_nearest(user, request.hospitals)

    return {
        "status": "success",
        "data": result
    }