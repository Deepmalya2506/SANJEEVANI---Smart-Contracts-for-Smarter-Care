from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# --- Equipment Asset Models ---
class EquipmentAssetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    equipment_type: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    serial_number: str | None = Field(default=None, max_length=100)
    condition_status: str = Field(default="OPERATIONAL", max_length=50)
    shareable: bool = True
    hourly_rate: float = Field(ge=0.0)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    metadata: dict | None = None


class EquipmentAssetResponse(BaseModel):
    asset_id: UUID
    hospital_id: UUID
    equipment_type: str
    name: str
    serial_number: str | None
    condition_status: str
    availability_status: str
    shareable: bool
    hourly_rate: float | None
    latitude: float | None
    longitude: float | None
    created_at: datetime


# --- Inventory Search & Aggregation ---
class InventorySearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    equipment_type: str = Field(min_length=1, max_length=100)
    quantity: int = Field(default=1, gt=0)


class HospitalInventoryGroup(BaseModel):
    hospital_id: UUID
    hospital_name: str
    equipment_type: str
    available_count: int
    latitude: float | None
    longitude: float | None


# --- GIS Dispatch Request ---
class DispatchLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)


class DispatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    equipment_type: str = Field(min_length=1)
    quantity: int = Field(default=1, gt=0)
    location: DispatchLocation
    max_eta_minutes: int = Field(default=60, gt=0)


# --- Lifecycle Events ---
class LoanLifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    loan_id: UUID
    actor_id: UUID | None = None
    note: str | None = None