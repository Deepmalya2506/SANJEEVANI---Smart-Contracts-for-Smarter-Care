from fastapi import APIRouter
from app.services.dispatch_service import dispatch_logic

router = APIRouter()

@router.post("/dispatch")
def dispatch(data: dict):
    return dispatch_logic(data)

@router.post("/dispatch/preview")
def preview(data: dict):
    result = dispatch_logic(data)
    result.pop("loan", None)
    return result