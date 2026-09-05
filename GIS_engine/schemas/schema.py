from pydantic import BaseModel, ConfigDict, Field
from typing import List

class Coordinate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lon: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)

class MatrixRequest(BaseModel):
    """Adjacency Matrix for Route Availability Optimization"""
    model_config = ConfigDict(extra="forbid")

    locations: List[Coordinate]

class MatrixResponse(BaseModel):
    """Connectivity Results"""
    distances: List[List[float]]
    durations: List[List[float]]

class HospitalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    lon: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)

class NearestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_location: Coordinate
    hospitals: List[HospitalInput]

class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Coordinate
    destination: Coordinate

class IsochroneRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    center: Coordinate
    time_minutes: int = Field(gt=0, le=240)

class BestOptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: Coordinate
    hospitals: list[HospitalInput]