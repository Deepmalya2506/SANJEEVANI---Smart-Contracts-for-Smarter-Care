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