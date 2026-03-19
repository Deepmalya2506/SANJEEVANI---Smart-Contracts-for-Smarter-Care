from pydantic import BaseModel

class Hospital(BaseModel):
    hospital_id: str
    name: str
    wallet: str
    location: str