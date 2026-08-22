from pydantic import BaseModel, ConfigDict, Field


class InventorySearchQuery(BaseModel):
	model_config = ConfigDict(extra="forbid")

	equipment_type: int = Field(gt=0)
	quantity: int = Field(gt=0)


class DispatchLocation(BaseModel):
	model_config = ConfigDict(extra="forbid")

	lat: float = Field(ge=-90, le=90)
	lon: float = Field(ge=-180, le=180)


class DispatchRequest(BaseModel):
	model_config = ConfigDict(extra="forbid")

	equipment_type: int = Field(gt=0)
	quantity: int = Field(gt=0)
	location: DispatchLocation
	skip_blockchain: bool = False
	from_hospital_id: str | None = None
	to_hospital_id: str | None = None


class LoanCreatedEvent(BaseModel):
	model_config = ConfigDict(extra="forbid")

	hospital_id: str = Field(min_length=1)


class LoanEvent(BaseModel):
	model_config = ConfigDict(extra="forbid")

	loan_id: int = Field(ge=0)
