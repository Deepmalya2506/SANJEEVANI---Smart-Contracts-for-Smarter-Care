from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class Coordinate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    lat: float = Field(ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(ge=-180.0, le=180.0, description="Longitude in decimal degrees")

class HospitalCandidate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    hospital_id: str = Field(description="UUID string of the registered hospital organization")
    hospital_name: str = Field(default="", description="Registered facility name")
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    available_count: int = Field(default=1, ge=0, description="Number of shareable units currently AVAILABLE")
    avg_hourly_rate: float = Field(default=0.0, ge=0.0, description="Hourly rental rate in INR")
    h3_cell: Optional[str] = Field(default=None, description="Pre-computed H3 hex cell string")
    wallet_address: Optional[str] = Field(default=None, description="EVM wallet address of hospital")

class MatrixRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    locations: List[Coordinate]

class NearestRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_location: Coordinate
    hospitals: List[HospitalCandidate]

class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: Coordinate
    destination: Coordinate

class FeasibilityRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    origin: Coordinate
    candidates: List[HospitalCandidate]
    max_eta_minutes: int = Field(default=60, gt=0, le=300)
    h3_resolution: int = Field(default=7, ge=5, le=10)
    traffic_mode: Optional[str] = Field(default=None, description="Optional override: NORMAL | SLOW | HEAVY")

class BestOptionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    origin: Coordinate
    hospitals: List[HospitalCandidate]
    max_eta_minutes: int = Field(default=60, gt=0, le=300)

class H3FootprintRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    center: Coordinate
    k_rings: int = Field(default=3, ge=1, le=10)
    resolution: int = Field(default=7, ge=5, le=10)

class IsochroneRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    center: Coordinate
    time_minutes: int = Field(gt=0, le=240)

class Map3DRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    center: Coordinate
    zoom: float = Field(default=15.0, ge=1.0, le=22.0)
    pitch: float = Field(default=60.0, ge=0.0, le=85.0)
    bearing: float = Field(default=-20.0, ge=-180.0, le=180.0)
    style: str = Field(default="satellite-3d", description="satellite-3d | street-3d | positron-dark")
    route_geometry: Optional[dict[str, Any]] = None
    traffic_status: Optional[str] = "NORMAL"