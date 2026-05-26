from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp_server.main import run_agent

app = FastAPI(title="Sanjeevani MCP")

# ✅ ADD THIS BLOCK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
def chat(data: dict):
    query = data["message"]
    hospital_id = data.get("hospital_id", None)

    response = run_agent(query, hospital_id) 
    return {"response": response}