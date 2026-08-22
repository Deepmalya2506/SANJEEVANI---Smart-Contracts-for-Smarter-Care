from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
	model_config = ConfigDict(extra="forbid")

	lat: float = Field(ge=-90, le=90)
	lon: float = Field(ge=-180, le=180)


class HospitalCreate(BaseModel):
	model_config = ConfigDict(extra="forbid")

	id: str = Field(min_length=1)
	wallet: str = Field(min_length=1)
	location: Location
	name: str | None = None
