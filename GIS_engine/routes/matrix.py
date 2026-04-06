from fastapi import APIRouter
from GIS_engine.schemas.schema import MatrixRequest
from GIS_engine.services.osrm_service import get_distance_matrix

router = APIRouter()

@router.post("/matrix")
def compute_matrix(request: MatrixRequest):
    coords = [(loc.lon, loc.lat) for loc in request.locations]

    result = get_distance_matrix(coords)

    return {
        "status": "success",
        "data": result
    }