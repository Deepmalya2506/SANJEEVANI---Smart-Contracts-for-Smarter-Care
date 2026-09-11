from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import ensure_payments_table_exists
from app.routes import hospitals, inventory, dispatch, events, payments


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure payments, loans, loan_state_events, and notifications exist in Supabase
    ensure_payments_table_exists()
    yield


app = FastAPI(
    title="SANJEEVANI Core API",
    description="Smart Contracts for Smarter Care — Real-Time Medical Resource Sharing Network",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hospitals.router)
app.include_router(inventory.router)
app.include_router(dispatch.router)
app.include_router(events.router)
app.include_router(payments.router)


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "SANJEEVANI Core API",
        "database": "Supabase PostgreSQL",
        "payments": "Razorpay Test Mode",
    }