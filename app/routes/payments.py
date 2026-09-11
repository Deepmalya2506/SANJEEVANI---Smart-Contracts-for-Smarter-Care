import json
from fastapi import APIRouter, Header, HTTPException, Request, status

from app.schemas.payments import PaymentOrderRequest, PaymentVerifyRequest
from app.services.razorpay_client import (
    apply_webhook,
    create_order,
    get_payment,
    verify_payment,
    verify_webhook,
)

router = APIRouter(tags=["payments"])


# ============================================================================
# Order Creation Endpoints (Frontend & Buildplan v1 compatible)
# ============================================================================
@router.post("/payments/orders")
@router.post("/api/v1/payments/create")
def create_payment_order(data: PaymentOrderRequest):
    return create_order(data.model_dump())


# ============================================================================
# Signature Verification Endpoints
# ============================================================================
@router.post("/payments/verify")
def verify_payment_signature(data: PaymentVerifyRequest):
    return verify_payment(data.model_dump())


# ============================================================================
# Payment Status Retrieval Endpoints
# ============================================================================
@router.get("/payments/{identifier}")
@router.get("/api/v1/payments/{identifier}")
def retrieve_payment(identifier: str):
    record = get_payment(identifier)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment record '{identifier}' not found in Supabase.",
        )
    return record


# ============================================================================
# Webhook Endpoints
# ============================================================================
@router.post("/payments/webhook")
@router.post("/api/v1/payments/webhook/razorpay")
async def payment_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
):
    body = await request.body()
    if not x_razorpay_signature or not verify_webhook(body, x_razorpay_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Razorpay webhook signature",
        )
    try:
        event_data = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed webhook JSON: {exc}",
        ) from exc

    return apply_webhook(event_data)