from fastapi import APIRouter
from app.core.database import inventory_collection

router = APIRouter()

@router.post("/events/loan-created")
def loan_created(data: dict):
    inventory_collection.update_many(
        {"hospital_id": data["hospital_id"], "status": "AVAILABLE"},
        {"$set": {"status": "RESERVED"}}
    )
    return {"status": "updated"}

@router.post("/events/delivery-confirmed")
def delivery_confirmed(data: dict):
    inventory_collection.update_many(
        {"loan_id": data["loan_id"]},
        {"$set": {"status": "IN_USE"}}
    )
    return {"status": "updated"}

@router.post("/events/loan-settled")
def loan_settled(data: dict):
    inventory_collection.update_many(
        {"loan_id": data["loan_id"]},
        {"$set": {"status": "AVAILABLE"}}
    )
    return {"status": "updated"}