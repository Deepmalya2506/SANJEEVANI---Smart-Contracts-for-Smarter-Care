from fastapi import APIRouter, HTTPException

from app.core.database import hospital_collection
from app.services.blockchain_client import is_registered_wallet
from app.schemas.hospital import HospitalCreate

import hashlib
import secrets

from datetime import datetime, timedelta

router = APIRouter()

# In-memory session store
# Use Redis/JWT in production.
_sessions = {}

@router.post("/hospitals")
def create_hospital(data: HospitalCreate):

    # ---------------------------------------------------------
    # CHECK DUPLICATE HOSPITAL ID
    # ---------------------------------------------------------

    existing_hospital = hospital_collection.find_one(
        {"id": data.id}
    )

    if existing_hospital:

        raise HTTPException(
            status_code=409,
            detail="Hospital ID already exists"
        )

    # ---------------------------------------------------------
    # NORMALIZE WALLET
    # ---------------------------------------------------------

    wallet = data.wallet.strip()

    # ---------------------------------------------------------
    # CHECK BLOCKCHAIN REGISTRATION
    # ---------------------------------------------------------

    try:

        registered = is_registered_wallet(
            wallet
        )

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Blockchain unavailable: {str(e)}"
        )

    if not registered:

        raise HTTPException(
            status_code=400,
            detail=(
                "Wallet is not registered on the "
                "Sanjeevani blockchain. "
                "Register the hospital wallet first."
            )
        )

    # ---------------------------------------------------------
    # CHECK WALLET NOT ALREADY LINKED
    # ---------------------------------------------------------

    existing_wallet = hospital_collection.find_one(
        {"wallet": wallet}
    )

    if existing_wallet:

        raise HTTPException(
            status_code=409,
            detail=(
                "This wallet is already linked to "
                "another hospital."
            )
        )

    # ---------------------------------------------------------
    # BUILD MONGODB DOCUMENT
    # ---------------------------------------------------------

    hospital_document = {

        "id": data.id,

        "name": data.name,

        "wallet": wallet,

        "location": {
            "lat": data.location.lat,
            "lon": data.location.lon
        }
    }

    # ---------------------------------------------------------
    # OPTIONAL LOGIN CREDENTIALS
    # ---------------------------------------------------------

    if data.email:

        hospital_document["email"] = data.email

    if data.password:

        hospital_document["password"] = (
            hashlib.sha256(
                data.password.encode()
            ).hexdigest()
        )

    # ---------------------------------------------------------
    # INSERT
    # ---------------------------------------------------------

    hospital_collection.insert_one(
        hospital_document
    )

    return {

        "success": True,

        "message": "Hospital created successfully",

        "hospital": {

            "id": data.id,

            "name": data.name,

            "wallet": wallet,

            "location": {
                "lat": data.location.lat,
                "lon": data.location.lon
            }
        }
    }

@router.get("/hospitals")
def get_hospitals():
    """List all registered hospitals (public endpoint for hospital selector)"""
    hospitals = list(hospital_collection.find({}, {"_id": 0}))
    return hospitals

@router.get("/hospitals/{hospital_id}")
def get_hospital(hospital_id: str):
    """Get details of a specific hospital"""
    hospital = hospital_collection.find_one({"id": hospital_id}, {"_id": 0})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital

@router.post("/hospitals/auth/login")
def hospital_login(data: dict):
    """
    Hospital admin login endpoint.
    Validates credentials and returns auth token + hospital info.
    
    Expected body:
    {
        "hospital_id": "h1",
        "email": "admin@hospital.org",
        "password": "securepass"
    }
    """
    hospital_id = data.get("hospital_id")
    email = data.get("email")
    password = data.get("password")
    
    if not all([hospital_id, email, password]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Fetch hospital from database
    hospital = hospital_collection.find_one({"id": hospital_id}, {"_id": 0})
    if not hospital:
        raise HTTPException(status_code=401, detail="Hospital not found")
    
    # Validate credentials (in production, use proper password hashing like bcrypt)
    stored_password = hospital.get("password", "")
    hashed_input = hashlib.sha256(password.encode()).hexdigest()
    
    if stored_password != hashed_input and stored_password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate session token
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "hospital_id": hospital_id,
        "hospital_name": hospital.get("name"),
        "email": email,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    
    return {
        "success": True,
        "token": token,
        "hospital": {
            "id": hospital_id,
            "name": hospital.get("name"),
            "location": hospital.get("location"),
            "wallet": hospital.get("wallet")
        },
        "message": f"Successfully logged in as {hospital.get('name')}"
    }

@router.post("/hospitals/auth/verify")
def verify_token(data: dict):
    """Verify if a session token is valid"""
    token = data.get("token")
    
    if not token or token not in _sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    session = _sessions[token]
    
    if session["expires_at"] < datetime.now():
        _sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Token expired")
    
    return {
        "valid": True,
        "hospital_id": session["hospital_id"],
        "hospital_name": session["hospital_name"],
        "email": session["email"]
    }

@router.post("/hospitals/auth/logout")
def logout(data: dict):
    """Logout by invalidating session token"""
    token = data.get("token")
    if token in _sessions:
        _sessions.pop(token)
    
    return {"success": True, "message": "Logged out successfully"}
