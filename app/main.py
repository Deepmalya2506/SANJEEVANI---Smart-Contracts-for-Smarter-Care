from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import hospitals, inventory, dispatch, events

app = FastAPI()

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