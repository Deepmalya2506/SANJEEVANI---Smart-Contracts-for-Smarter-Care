from fastapi import FastAPI
from app.routes import hospitals, inventory, dispatch, events

app = FastAPI()

app.include_router(hospitals.router)
app.include_router(inventory.router)
app.include_router(dispatch.router)
app.include_router(events.router)