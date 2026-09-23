import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from GIS_engine.routes import routes, tiles

app = FastAPI(title="Sanjeevani GIS Engine", version="3.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Canonical GIS Routers
app.include_router(tiles.router, prefix="/gis")
app.include_router(routes.router, prefix="/gis")

@app.get("/route-map", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
def serve_route_map():
    file_path = os.path.join(os.path.dirname(__file__), "route_map.html")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>GIS Launchpad Route Map not found</h1>", status_code=404)