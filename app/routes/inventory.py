from fastapi import APIRouter, UploadFile, File
import pandas as pd
from app.core.database import inventory_collection
import uuid

router = APIRouter()

@router.post("/inventory/upload")
async def upload_inventory(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)

    records = df.to_dict(orient="records")

    for item in records:
        item["uid"] = str(uuid.uuid4())
        item["status"] = "AVAILABLE"

    inventory_collection.insert_many(records)

    return {"message": "Inventory uploaded"}

@router.get("/inventory/search")
def search_inventory(equipment_type: int, quantity: int):

    equipment_type = int(equipment_type)  # 🔥 force int

    results = inventory_collection.aggregate([
        {
            "$match": {
                "equipment_type": equipment_type,
                "status": "AVAILABLE"
            }
        },
        {
            "$group": {
                "_id": "$hospital_id",
                "count": {"$sum": 1}
            }
        },
        {
            "$match": {
                "count": {"$gte": quantity}
            }
        }
    ])

    print("QUERY:", {
        "equipment_type": equipment_type,
        "quantity": quantity
    })

    return list(results)

@router.get("/inventory/{hospital_id}")
def get_inventory(hospital_id: str):
    return list(inventory_collection.find(
        {"hospital_id": hospital_id},
        {"_id": 0}
    ))
