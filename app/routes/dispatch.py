from fastapi import APIRouter
from app.services.dispatch_service import dispatch_logic

from app.schemas.inventory import DispatchRequest

router = APIRouter()

@router.post("/dispatch")
def dispatch(data: DispatchRequest):
    return dispatch_logic(data.model_dump())

@router.post("/dispatch/preview")
def preview(data: DispatchRequest):
    result = dispatch_logic(data.model_dump())
    result.pop("loan", None)
    return result