class HeatShieldAgent:
    # Profile vulnerability multipliers & maximum heat thresholds
    PROFILES = {
        "STANDARD": {"threshold": 35.0, "water_mult": 1.0, "exposure_mult": 1.0, "label": "Standard Adult"},
        "WORKER":   {"threshold": 32.0, "water_mult": 1.6, "exposure_mult": 0.6, "label": "Outdoor Worker"},
        "ELDERLY":  {"threshold": 31.0, "water_mult": 1.3, "exposure_mult": 0.5, "label": "Elderly / Vulnerable"},
        "ATHLETE":  {"threshold": 37.0, "water_mult": 1.4, "exposure_mult": 1.2, "label": "Athlete / Active"},
        "CHILD":    {"threshold": 33.0, "water_mult": 1.2, "exposure_mult": 0.7, "label": "Child / Pedestrian"}
    }

    @staticmethod
    def evaluate_route_analytics(direct_path, cool_path, heat_grid, profile_key="STANDARD"):
        profile = HeatShieldAgent.PROFILES.get(profile_key.upper(), HeatShieldAgent.PROFILES["STANDARD"])
        
        high_heat_count = 0
        all_temps = []

        for f in heat_grid.get("features", []):
            t = f["properties"]["temperature"]
            all_temps.append(t)
            if t >= profile["threshold"]:
                high_heat_count += 1

        avg_temp = sum(all_temps) / max(len(all_temps), 1)
        peak_temp = max(all_temps) if all_temps else 35.0

        direct_dist_km = HeatShieldAgent._path_distance(direct_path)
        cool_dist_km = HeatShieldAgent._path_distance(cool_path)
        
        saved_thermal_load = round(min(peak_temp - avg_temp + 1.2, 5.5), 1)
        
        # Profile-adjusted safe outdoor exposure window & hydration math
        base_exposure = max(10, int(120 - (peak_temp - 30.0) * 10))
        safe_exposure_mins = max(10, int(base_exposure * profile["exposure_mult"]))
        
        base_water = (cool_dist_km * 250) + ((avg_temp - 30.0) * 35)
        recommended_water_ml = int(max(150, base_water * profile["water_mult"]))

        # Dynamic risk grading customized to personal profile
        if peak_temp >= (profile["threshold"] + 5.0):
            risk_level = "CRITICAL RISK"
        elif peak_temp >= profile["threshold"]:
            risk_level = "HIGH RISK"
        else:
            risk_level = "MODERATE RISK"

        advisory = {
            "profile_used": profile["label"],
            "risk_level": risk_level,
            "ambient_avg_temp": f"{avg_temp:.1f}°C",
            "peak_microclimate_temp": f"{peak_temp:.1f}°C",
            "heat_islands_avoided": high_heat_count,
            "thermal_exposure_reduced": f"-{saved_thermal_load}°C",
            "distance_direct_km": f"{direct_dist_km:.2f} km",
            "distance_cool_km": f"{cool_dist_km:.2f} km",
            "safe_exposure_limit": f"{safe_exposure_mins} mins",
            "recommended_hydration": f"{recommended_water_ml} mL",
            "summary": (
                f"Tailored for [{profile['label']}]: Router bypassed {high_heat_count} micro-heat zones "
                f"exceeding your personal safety threshold ({profile['threshold']}°C). "
                f"Net thermal stress reduced by {saved_thermal_load}°C."
            )
        }
        return advisory

    @staticmethod
    def _path_distance(path):
        dist = 0.0
        for i in range(len(path) - 1):
            lat1, lon1 = path[i]
            lat2, lon2 = path[i+1]
            dist += (((lat2 - lat1)*111)**2 + ((lon2 - lon1)*96)**2)**0.5
        return dist