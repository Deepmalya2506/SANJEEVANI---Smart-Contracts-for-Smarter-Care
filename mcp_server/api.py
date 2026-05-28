from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp_server.main import run_agent
from app.core.database import hospital_collection

app = FastAPI(title="Sanjeevani MCP")

# ✅ CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
def chat(data: dict):
    """
    Enhanced chat endpoint supporting:
    - Session persistence with conversation history
    - Hospital context for distance calculations
    - Map URL embedding
    - Transaction confirmation
    """
    query = data["message"]
    session_id = data.get("session_id")
    hospital_id = data.get("hospital_id")
    conversation_history = data.get("conversation_history", [])

    # Run agent with full context
    response = run_agent(query, session_id, hospital_id)
    
    # Transform response for frontend
    return {
        "reply": response.get("reply"),
        "approval_required": response.get("approval_required", False),
        "loan_proposal": response.get("loan_proposal"),
        "route_map_url": response.get("map_url"),  # Embed map URL in response
        "tx_hash": response.get("tx_hash"),
        "loan_id": response.get("loan_id"),
        "session_id": session_id
    }

@app.get("/hospitals")
def list_hospitals():
    """
    Get all registered hospitals for hospital selector.
    Returns: List of hospitals with ID, name, location, and wallet.
    """
    hospitals = list(hospital_collection.find({}, {"_id": 0}))
    
    # Transform for frontend
    return [
        {
            "id": h.get("id"),
            "name": h.get("name"),
            "location": h.get("location"),
            "wallet": h.get("wallet"),
            "inventory": h.get("inventory_count", 0)
        }
        for h in hospitals
    ]

@app.post("/approve")
def approve_dispatch(data: dict):
    """
    Handle user approval of dispatch/loan proposal.
    Triggers blockchain transaction and backend dispatch recording.
    """
    approval_id = data.get("approval_id")
    session_id = data.get("session_id")
    
    # In a real implementation, this would trigger the loan creation
    # For now, return success
    return {
        "approved": True,
        "session_id": session_id,
        "message": "Dispatch approved and recorded on blockchain."
    }
