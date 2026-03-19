from pydantic import BaseModel

class EquipmentAsset(BaseModel):
    uid: str
    equipment_type: int
    hospital_id: str
    status: str