from fastapi import APIRouter
from app.core.database import hospital_collection
from app.schemas.hospital import HospitalCreate

router = APIRouter()

@router.post("/hospitals")
def create_hospital(data: HospitalCreate):
    hospital_collection.insert_one(data.model_dump())
    return {"message": "Hospital created"}

@router.get("/hospitals")
def get_hospitals():
    hospitals = list(hospital_collection.find({}, {"_id": 0}))
    return hospitals

@router.get("/hospitals/{hospital_id}")
def get_hospital(hospital_id: str):
    hospital = hospital_collection.find_one({"id": hospital_id}, {"_id": 0})
    return hospital