from pydantic import BaseModel, ConfigDict, Field


class PaymentOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_rupees: int = Field(gt=0)
    currency: str = Field(default="INR", pattern="^[A-Z]{3}$")
    receipt: str | None = Field(default=None, min_length=1, max_length=40)
    loan_reference: str | None = Field(default=None, min_length=1, max_length=80)
    notes: dict[str, str] = Field(default_factory=dict, max_length=10)


class PaymentVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    razorpay_order_id: str = Field(min_length=1)
    razorpay_payment_id: str = Field(min_length=1)
    razorpay_signature: str = Field(min_length=1)


class PaymentRefundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_paise: int | None = Field(default=None, gt=0)
    notes: dict[str, str] = Field(default_factory=dict, max_length=10)