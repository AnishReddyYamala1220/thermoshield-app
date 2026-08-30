import os
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv()

class FortyGuardClient:
    def __init__(self):
        self.api_key = os.getenv("FORTYGUARD_API_KEY")
        self.base_url = "https://api.fortyguard.com"
        self.headers = {
            "api-key": self.api_key or "",
            "Content-Type": "application/json"
        }

    def fetch_heatmap(self, polygon_coords, date_str="2024-07-15", time_str="14:00"):
        # Fallback to simulated 20m spatial resolution grid if key is unconfigured or placeholder
        if not self.api_key or self.api_key in ["your_optional_api_key_here", "your_actual_api_key_here"]:
            print("[FortyGuard Dev Engine] Running with simulated 20m² thermal mesh.")
            return self._generate_mock_thermal_grid(polygon_coords)

        payload = {
            "polygon_aoi": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [polygon_coords]
                    }
                }]
            },
            "date_time_start_date": date_str,
            "date_time_start_time": time_str,
            "date_time_filter_type": 1,
            "granularity": 20
        }

        try:
            res = requests.post(f"{self.base_url}/v1/heatmap", json=payload, headers=self.headers, timeout=10)
            res.raise_for_status()
            activity_id = res.json().get("activity_id")

            # Async Polling Pattern
            for _ in range(12):
                time.sleep(4)
                status_res = requests.get(f"{self.base_url}/v1/status/{activity_id}", headers=self.headers)
                data = status_res.json()
                if data.get("status") == "succeeded":
                    return data.get("data")
                elif data.get("status") == "failed":
                    break
        except Exception as e:
            print(f"[FortyGuard API] Warning: API request failed ({e}). Falling back to spatial simulator.")
        
        return self._generate_mock_thermal_grid(polygon_coords)

    def _generate_mock_thermal_grid(self, polygon_coords):
        """Generates 20m spatial resolution heat grid matching FortyGuard schema."""
        lats = [pt[1] for pt in polygon_coords]
        lons = [pt[0] for pt in polygon_coords]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        features = []
        step = 0.0005  # ~20m grid resolution
        
        curr_lat = min_lat
        while curr_lat < max_lat:
            curr_lon = min_lon
            while curr_lon < max_lon:
                center_lat = (min_lat + max_lat) / 2
                center_lon = (min_lon + max_lon) / 2
                dist_from_center = ((curr_lat - center_lat)**2 + (curr_lon - center_lon)**2)**0.5
                
                base_temp = 32.0 + (random.random() * 2.0)
                if dist_from_center < 0.0015:
                    base_temp += 8.5  # Creates a 40°C+ heat hazard hotspot
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [curr_lon, curr_lat],
                            [curr_lon + step, curr_lat],
                            [curr_lon + step, curr_lat + step],
                            [curr_lon, curr_lat + step],
                            [curr_lon, curr_lat]
                        ]]
                    },
                    "properties": {
                        "temperature": round(base_temp, 2),
                        "unit": "Celsius"
                    }
                })
                curr_lon += step
            curr_lat += step

        return {"type": "FeatureCollection", "features": features}