from fastapi import FastAPI
from routes import matrix, nearest
from routes import routes

app = FastAPI(title="Sanjeevani GIS Engine")

app.include_router(matrix.router, prefix="/gis")
app.include_router(nearest.router, prefix="/gis")
app.include_router(routes.router, prefix="/gis")