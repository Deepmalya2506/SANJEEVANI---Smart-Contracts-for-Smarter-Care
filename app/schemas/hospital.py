from pydantic import BaseModel, Field


class HospitalLocation(BaseModel):

    lat: float
    lon: float


class HospitalCreate(BaseModel):

    id: str = Field(
        min_length=1,
        max_length=100
    )

    name: str = Field(
        min_length=1,
        max_length=200
    )

    wallet: str

    location: HospitalLocation

    email: str | None = None

    password: str | None = None