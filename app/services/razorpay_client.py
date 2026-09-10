import hashlib
import hmac
import uuid

import razorpay
from fastapi import HTTPException

from app.core.config import settings
from app.core.database import payment_collection


def _client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Razorpay test credentials are not configured",
        )
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_order(data: dict) -> dict:
    client = _client()
    receipt = data.get("receipt") or f"loan_{uuid.uuid4().hex[:24]}"
    amount_paise = data["amount_rupees"] * 100
    try:
        order = client.order.create(
            {
                "amount": amount_paise,
                "currency": data["currency"],
                "receipt": receipt,
                "notes": data.get("notes", {}),
            }
        )
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Razorpay order creation failed: {error}") from error
    payment_collection.insert_one({
        "order_id": order["id"],
        "loan_reference": data.get("loan_reference"),
        "amount_paise": order["amount"],
        "amount_rupees": order["amount"] // 100,
        "currency": order["currency"],
        "status": "PAYMENT_PENDING",
        "receipt": receipt,
    })
    return {
        "order_id": order["id"],
        "amount_paise": order["amount"],
        "currency": order["currency"],
        "key_id": settings.RAZORPAY_KEY_ID,
        "status": "PAYMENT_PENDING",
    }


def verify_payment(data: dict) -> dict:
    client = _client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        })
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Razorpay payment verification failed: {error}") from error
    payment_collection.update_one(
        {"order_id": data["razorpay_order_id"]},
        {"$set": {
            "payment_id": data["razorpay_payment_id"],
            "status": "PAYMENT_AUTHORIZED",
        }},
    )
    return {"status": "PAYMENT_AUTHORIZED", "payment_id": data["razorpay_payment_id"]}


def verify_webhook(body: bytes, signature: str) -> bool:
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret:
        raise HTTPException(status_code=503, detail="Razorpay webhook secret is not configured")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def apply_webhook(event: dict) -> dict:
    payload = event.get("payload", {})
    payment = payload.get("payment", {}).get("entity", {})
    order_id = payment.get("order_id")
    if not order_id:
        return {"status": "ignored"}
    event_name = event.get("event")
    status = {
        "payment.captured": "PAYMENT_CAPTURED",
        "order.paid": "PAYMENT_CAPTURED",
        "payment.failed": "PAYMENT_FAILED",
        "refund.processed": "REFUNDED",
    }.get(event_name)
    if status:
        payment_collection.update_one(
            {"order_id": order_id},
            {"$set": {"status": status, "payment_id": payment.get("id")}},
        )
    return {"status": status or "ignored"}