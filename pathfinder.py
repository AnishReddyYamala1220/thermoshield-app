import heapq
import math

class HeatWeightedPathfinder:
    def __init__(self, heat_grid, grid_size=0.0003, hour_of_day=14): # Default 2:00 PM peak solar radiation
        self.grid_size = grid_size
        self.temp_map = {}
        self.hour_of_day = hour_of_day
        self._process_heat_grid(heat_grid)

    def _process_heat_grid(self, heat_grid):
        for feature in heat_grid.get("features", []):
            coords = feature["geometry"]["coordinates"][0]
            avg_lon = sum(pt[0] for pt in coords[:4]) / 4.0
            avg_lat = sum(pt[1] for pt in coords[:4]) / 4.0
            temp = feature["properties"]["temperature"]
            
            grid_key = (round(avg_lat / self.grid_size), round(avg_lon / self.grid_size))
            self.temp_map[grid_key] = temp

    def get_node_temp(self, lat, lon):
        key = (round(lat / self.grid_size), round(lon / self.grid_size))
        return self.temp_map.get(key, 33.0)

    def _calculate_solar_intensity(self):
        """Calculates relative solar radiation factor based on time of day (0.0 at night, 1.0 at solar noon)."""
        if self.hour_of_day < 6 or self.hour_of_day > 19:
            return 0.1  # Minimal nocturnal ground radiation
        return math.sin(math.pi * (self.hour_of_day - 6) / 13.0)

    def find_cool_route(self, start, end):
        start_node = (round(start[1] / self.grid_size), round(start[0] / self.grid_size))
        end_node = (round(end[1] / self.grid_size), round(end[0] / self.grid_size))

        open_set = []
        heapq.heappush(open_set, (0, start_node))
        
        came_from = {}
        g_score = {start_node: 0}
        
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]

        solar_factor = self._calculate_solar_intensity()

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end_node:
                path = []
                while current in came_from:
                    path.append([current[0] * self.grid_size, current[1] * self.grid_size])
                    current = came_from[current]
                path.append([start_node[0] * self.grid_size, start_node[1] * self.grid_size])
                path.reverse()
                return path

            for dlat, dlon in directions:
                neighbor = (current[0] + dlat, current[1] + dlon)
                
                move_dist = math.hypot(dlat, dlon) * self.grid_size * 111000  # meters
                node_lat = neighbor[0] * self.grid_size
                node_lon = neighbor[1] * self.grid_size
                temp = self.get_node_temp(node_lat, node_lon)
                
                # Dynamic Solar Radiation & Thermal Penalty calculation
                thermal_excess = max(0, temp - 34.0)
                heat_penalty = (thermal_excess ** 2.1) * (1.0 + solar_factor * 0.8) * 12.0
                step_cost = move_dist + heat_penalty

                tentative_g = g_score[current] + step_cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    
                    h = math.hypot(end_node[0] - neighbor[0], end_node[1] - neighbor[1]) * self.grid_size * 111000
                    f_score = tentative_g + h
                    heapq.heappush(open_set, (f_score, neighbor))

        return [[start[1], start[0]], [(start[1]+end[1])/2, (start[0]+end[0])/2], [end[1], end[0]]]