from fastapi import FastAPI
from GIS_engine.routes import matrix, nearest
from GIS_engine.routes import routes

app = FastAPI(title="Sanjeevani GIS Engine")

app.include_router(matrix.router, prefix="/gis")
app.include_router(nearest.router, prefix="/gis")
app.include_router(routes.router, prefix="/gis")