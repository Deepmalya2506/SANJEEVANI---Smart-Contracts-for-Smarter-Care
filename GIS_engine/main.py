from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from GIS_engine.routes import matrix, nearest
from GIS_engine.routes import routes

app = FastAPI(title="Sanjeevani GIS Engine")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(matrix.router, prefix="/gis")
app.include_router(nearest.router, prefix="/gis")
app.include_router(routes.router, prefix="/gis")