from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PaymentOrderRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    amount_rupees: float = Field(gt=0, description="Amount in INR rupees (e.g. 1850 or 1850.50)")
    currency: str = Field(default="INR", pattern="^[A-Z]{3}$")
    receipt: str | None = Field(default=None, min_length=1, max_length=100)
    loan_reference: str | None = Field(default=None, min_length=1, max_length=100)
    notes: dict[str, Any] = Field(default_factory=dict)


class PaymentVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    razorpay_order_id: str = Field(min_length=1)
    razorpay_payment_id: str = Field(min_length=1)
    razorpay_signature: str = Field(min_length=1)


class PaymentRefundRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    amount_paise: int | None = Field(default=None, gt=0)
    notes: dict[str, Any] = Field(default_factory=dict)