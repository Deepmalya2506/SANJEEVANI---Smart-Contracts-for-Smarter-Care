from fastapi import FastAPI
from routes import matrix

app = FastAPI(title="Sanjeevani GIS Engine")

app.include_router(matrix.router, prefix="/gis")