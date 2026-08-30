from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fortyguard_client import FortyGuardClient
from pathfinder import HeatWeightedPathfinder
from agent import HeatShieldAgent

app = FastAPI(title="ThermoShield AI - Solar & Infrastructure Pathfinder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

fg_client = FortyGuardClient()

class RouteRequest(BaseModel):
    origin: list[float]
    destination: list[float]
    user_profile: str = "STANDARD"
    hour_of_day: int = 14

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/plan-route")
def plan_route(req: RouteRequest):
    min_lon = min(req.origin[0], req.destination[0]) - 0.003
    max_lon = max(req.origin[0], req.destination[0]) + 0.003
    min_lat = min(req.origin[1], req.destination[1]) - 0.003
    max_lat = max(req.origin[1], req.destination[1]) + 0.003

    polygon_aoi = [
        [min_lon, min_lat],
        [max_lon, min_lat],
        [max_lon, max_lat],
        [min_lon, max_lat],
        [min_lon, min_lat]
    ]

    heat_grid = fg_client.fetch_heatmap(polygon_aoi)

    # Initialize pathfinder with Solar Azimuth time component
    router = HeatWeightedPathfinder(heat_grid, hour_of_day=req.hour_of_day)
    cool_path = router.find_cool_route(req.origin, req.destination)

    direct_path = [
        [req.origin[1], req.origin[0]],
        [(req.origin[1] + req.destination[1]) / 2, (req.origin[0] + req.destination[0]) / 2],
        [req.destination[1], req.destination[0]]
    ]

    # Generate Infrastructure Nodes (Water Fountains & Cooling Shelters)
    refill_stations = [
        {"name": "Hydration Station A", "lat": req.origin[1] + 0.0012, "lon": req.origin[0] + 0.0015, "type": "fountain"},
        {"name": "Public Cooling Center", "lat": req.destination[1] - 0.0010, "lon": req.destination[0] - 0.0012, "type": "shelter"}
    ]

    analytics = HeatShieldAgent.evaluate_route_analytics(
        direct_path, cool_path, heat_grid, profile_key=req.user_profile
    )

    return {
        "status": "success",
        "heat_grid": heat_grid,
        "direct_path": direct_path,
        "cool_path": cool_path,
        "infrastructure": refill_stations,
        "analytics": analytics
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)