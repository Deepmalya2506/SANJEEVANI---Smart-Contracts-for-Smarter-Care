from fastapi import APIRouter
from app.core.database import inventory_collection
from app.schemas.inventory import LoanCreatedEvent, LoanEvent

router = APIRouter()

@router.post("/events/loan-created")
def loan_created(data: LoanCreatedEvent):
    data = data.model_dump()
    inventory_collection.update_many(
        {"hospital_id": data["hospital_id"], "status": "AVAILABLE"},
        {"$set": {"status": "RESERVED"}}
    )
    return {"status": "updated"}

@router.post("/events/delivery-confirmed")
def delivery_confirmed(data: LoanEvent):
    data = data.model_dump()
    inventory_collection.update_many(
        {"loan_id": data["loan_id"]},
        {"$set": {"status": "IN_USE"}}
    )
    return {"status": "updated"}

@router.post("/events/loan-settled")
def loan_settled(data: LoanEvent):
    data = data.model_dump()
    inventory_collection.update_many(
        {"loan_id": data["loan_id"]},
        {"$set": {"status": "AVAILABLE"}}
    )
    return {"status": "updated"}