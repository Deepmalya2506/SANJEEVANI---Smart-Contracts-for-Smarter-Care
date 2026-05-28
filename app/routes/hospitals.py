from fastapi import APIRouter, HTTPException
from app.core.database import hospital_collection
import hashlib
import json
from datetime import datetime, timedelta
import secrets

router = APIRouter()

# In-memory session store (use Redis in production)
_sessions = {}

@router.post("/hospitals")
def create_hospital(data: dict):
    hospital_collection.insert_one(data)
    return {"message": "Hospital created"}

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
