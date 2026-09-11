import re
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# --- Step 1: Pre-Verification Schemas ---
class HFRVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    mvp_hfr_id: str = Field(min_length=1, max_length=100)
    hospital_name: str = Field(min_length=1, max_length=300)


class HFRVerificationResponse(BaseModel):
    verified: bool
    directory_match: bool
    registration_allowed: bool
    mvp_hfr_id: str
    hospital_name: str | None = None
    message: str


# --- Step 2: Account Creation / Signup Schemas ---
class HospitalSignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    mvp_hfr_id: str = Field(min_length=1, max_length=100)
    hospital_name: str = Field(min_length=1, max_length=300)
    admin_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class HospitalSignupResponse(BaseModel):
    hospital_id: UUID
    user_id: UUID
    auth_user_id: UUID
    email: EmailStr
    profile_status: str
    message: str


# --- Step 3: Profile Completion Schemas ---
class ProfileSetupData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    wallet_address: str = Field(min_length=42, max_length=42)
    network: str = Field(min_length=1, max_length=100)
    upi_id: str = Field(min_length=3, max_length=200)
    provider: str = Field(min_length=1, max_length=100)

    @field_validator("wallet_address")
    @classmethod
    def validate_evm_wallet(cls, value: str) -> str:
        if not re.match(r"^0x[a-fA-F0-9]{40}$", value):
            raise ValueError("wallet_address must be a valid 42-character hexadecimal EVM address starting with '0x'")
        return value.lower()

    @field_validator("upi_id")
    @classmethod
    def validate_upi(cls, value: str) -> str:
        if "@" not in value or len(value.split("@")) != 2 or not all(value.split("@")):
            raise ValueError("upi_id must adhere to standard VPA format (e.g., user@bank)")
        return value


class CompleteProfileResponse(BaseModel):
    hospital_id: UUID
    user_id: UUID
    profile_completed: bool
    profile_status: str
    message: str


# --- Authenticated Identity Summary ---
class CurrentUserContext(BaseModel):
    user_id: UUID
    auth_user_id: UUID
    hospital_id: UUID
    admin_name: str
    user_mail: str
    profile_completed: bool
    hospital_name: str
    mvp_hfr_id: str
    profile_status: str
    verification_status: str