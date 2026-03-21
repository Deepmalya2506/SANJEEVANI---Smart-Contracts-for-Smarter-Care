from pydantic import BaseModel
from typing import List

class Coordinate(BaseModel):
    lon: float
    lat: float

class MatrixRequest(BaseModel):
    """Adjacency Matrix for Route Availability Optimization"""
    locations: List[Coordinate]

class MatrixResponse(BaseModel):
    """Connectivity Results"""
    distances: List[List[float]]
    durations: List[List[float]]

class HospitalInput(BaseModel):
    id: str
    lon: float
    lat: float

class NearestRequest(BaseModel):
    user_location: Coordinate
    hospitals: List[HospitalInput]

class RouteRequest(BaseModel):
    source: Coordinate
    destination: Coordinate

class IsochroneRequest(BaseModel):
    center: Coordinate
    time_minutes: int