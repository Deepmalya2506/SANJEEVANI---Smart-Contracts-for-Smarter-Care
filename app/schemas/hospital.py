from pydantic import BaseModel, ConfigDict, Field, field_validator


class Location(BaseModel):
	model_config = ConfigDict(extra="forbid")

	lat: float = Field(ge=-90, le=90)
	lon: float = Field(ge=-180, le=180)


class HospitalCreate(BaseModel):
	model_config = ConfigDict(extra="forbid")

	id: str = Field(min_length=1)
	wallet: str = Field(min_length=42, max_length=42)
	location: Location
	name: str | None = None

	@field_validator("wallet")
	@classmethod
	def validate_wallet(cls, value: str) -> str:
		if not value.startswith("0x"):
			raise ValueError("wallet must start with 0x")
		try:
			int(value[2:], 16)
		except ValueError as error:
			raise ValueError("wallet must contain hexadecimal characters") from error
		return value
