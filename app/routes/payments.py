import json

from fastapi import APIRouter, Header, Request

from app.schemas.payments import PaymentOrderRequest, PaymentVerifyRequest
from app.services.razorpay_client import (
    apply_webhook,
    create_order,
    verify_payment,
    verify_webhook,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/orders")
def create_payment_order(data: PaymentOrderRequest):
    return create_order(data.model_dump())


@router.post("/verify")
def verify_payment_signature(data: PaymentVerifyRequest):
    return verify_payment(data.model_dump())


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
):
    body = await request.body()
    if not x_razorpay_signature or not verify_webhook(body, x_razorpay_signature):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid Razorpay webhook signature")
    return apply_webhook(json.loads(body))