from typing import Dict, List, Set, Tuple
import math
import requests
import os
from dotenv import load_dotenv
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta

load_dotenv()

class Graph:
    def __init__(self):
        self.vertices: Dict[str, Dict[str, float]] = {}
    
    def add_vertex(self, vertex: str):
        if vertex not in self.vertices:
            self.vertices[vertex] = {}
    
    def add_edge(self, from_vertex: str, to_vertex: str, distance: float):
        self.add_vertex(from_vertex)
        self.add_vertex(to_vertex)
        self.vertices[from_vertex][to_vertex] = distance
        self.vertices[to_vertex][from_vertex] = distance  # For undirected graph
    
    def get_neighbors(self, vertex: str) -> List[str]:
        return list(self.vertices[vertex].keys())
    
    def get_distance(self, from_vertex: str, to_vertex: str) -> float:
        return self.vertices[from_vertex][to_vertex]

def get_google_maps_distance(origin: Tuple[float, float], destination: Tuple[float, float]) -> float:
    """
    Get the actual road distance between two points using Google Maps Distance Matrix API.
    Returns distance in kilometers.
    """
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
    
    params = {
        'origins': f"{origin[0]},{origin[1]}",
        'destinations': f"{destination[0]},{destination[1]}",
        'key': api_key,
        'mode': 'driving'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == 'OK':
            return data['rows'][0]['elements'][0]['distance']['value'] / 1000  # Convert meters to kilometers
        else:
            # Fallback to Haversine if API fails
            return calculate_haversine_distance(origin, destination)
    except:
        # Fallback to Haversine if API fails
        return calculate_haversine_distance(origin, destination)

def calculate_haversine_distance(origin: Tuple[float, float], destination: Tuple[float, float]) -> float:
    """
    Calculate the distance between two points using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1 = origin
    lat2, lon2 = destination
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def dijkstra(graph: Graph, start: str) -> Tuple[Dict[str, float], Dict[str, str]]:
    """
    Implementation of Dijkstra's algorithm for finding shortest paths.
    Returns a tuple of (distances, previous_vertices).
    """
    distances = {vertex: float('infinity') for vertex in graph.vertices}
    distances[start] = 0
    previous = {vertex: None for vertex in graph.vertices}
    unvisited: Set[str] = set(graph.vertices)
    
    while unvisited:
        current = min(unvisited, key=lambda x: distances[x])
        
        if distances[current] == float('infinity'):
            break
            
        unvisited.remove(current)
        
        for neighbor in graph.get_neighbors(current):
            if neighbor in unvisited:
                distance = distances[current] + graph.get_distance(current, neighbor)
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
    
    return distances, previous

def floyd_warshall(locations: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Implementation of Floyd-Warshall algorithm for all-pairs shortest paths.
    Returns a tuple of (distance matrix, next matrix).
    """
    n = len(locations)
    dist = np.full((n, n), float('inf'))
    next_node = np.full((n, n), -1, dtype=int)
    
    # Initialize distance matrix
    for i in range(n):
        dist[i][i] = 0
        for j in range(i + 1, n):
            distance = calculate_haversine_distance(
                (locations[i]['latitude'], locations[i]['longitude']),
                (locations[j]['latitude'], locations[j]['longitude'])
            )
            dist[i][j] = distance
            dist[j][i] = distance
            next_node[i][j] = j
            next_node[j][i] = i
    
    # Floyd-Warshall algorithm
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][j] > dist[i][k] + dist[k][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]
    
    return dist, next_node

def get_path_floyd_warshall(next_node: np.ndarray, start: int, end: int) -> List[int]:
    """
    Reconstruct the path from start to end using the next_node matrix.
    """
    if next_node[start][end] == -1:
        return []
    
    path = [start]
    while start != end:
        start = next_node[start][end]
        path.append(start)
    return path

def tsp_brute_force(locations: List[Dict]) -> List[int]:
    """
    Implementation of TSP using brute force (for small number of locations).
    Returns the optimal route as a list of indices.
    """
    n = len(locations)
    if n > 10:  # Brute force is too slow for more than 10 locations
        return nearest_neighbor(locations)
    
    from itertools import permutations
    
    min_distance = float('inf')
    best_route = None
    
    # Try all possible permutations
    for route in permutations(range(n)):
        distance = 0
        for i in range(n - 1):
            distance += calculate_haversine_distance(
                (locations[route[i]]['latitude'], locations[route[i]]['longitude']),
                (locations[route[i + 1]]['latitude'], locations[route[i + 1]]['longitude'])
            )
        distance += calculate_haversine_distance(
            (locations[route[-1]]['latitude'], locations[route[-1]]['longitude']),
            (locations[route[0]]['latitude'], locations[route[0]]['longitude'])
        )
        
        if distance < min_distance:
            min_distance = distance
            best_route = route
    
    return list(best_route)

def nearest_neighbor(locations: List[Dict]) -> List[int]:
    """
    Implementation of the Nearest Neighbor algorithm for TSP.
    Returns a list of indices representing the optimized route.
    """
    if not locations:
        return []
    
    n = len(locations)
    visited = [False] * n
    route = [0]  # Start with the first location
    visited[0] = True
    
    for _ in range(n - 1):
        current = route[-1]
        min_dist = float('infinity')
        next_loc = -1
        
        for i in range(n):
            if not visited[i]:
                dist = calculate_haversine_distance(
                    (locations[current]['latitude'], locations[current]['longitude']),
                    (locations[i]['latitude'], locations[i]['longitude'])
                )
                if dist < min_dist:
                    min_dist = dist
                    next_loc = i
        
        route.append(next_loc)
        visited[next_loc] = True
    
    return route

def two_opt_swap(route: List[int], i: int, j: int) -> List[int]:
    """
    Perform a 2-opt swap on the route.
    """
    new_route = route[:i]
    new_route.extend(reversed(route[i:j+1]))
    new_route.extend(route[j+1:])
    return new_route

def two_opt(locations: List[Dict], initial_route: List[int]) -> List[int]:
    """
    Implementation of the 2-opt algorithm for improving an existing route.
    """
    n = len(initial_route)
    best_route = initial_route.copy()
    improved = True
    
    while improved:
        improved = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                # Calculate the change in distance
                old_dist = (
                    calculate_haversine_distance(
                        (locations[best_route[i-1]]['latitude'], locations[best_route[i-1]]['longitude']),
                        (locations[best_route[i]]['latitude'], locations[best_route[i]]['longitude'])
                    ) +
                    calculate_haversine_distance(
                        (locations[best_route[j]]['latitude'], locations[best_route[j]]['longitude']),
                        (locations[best_route[j+1]]['latitude'], locations[best_route[j+1]]['longitude'])
                    )
                )
                
                new_dist = (
                    calculate_haversine_distance(
                        (locations[best_route[i-1]]['latitude'], locations[best_route[i-1]]['longitude']),
                        (locations[best_route[j]]['latitude'], locations[best_route[j]]['longitude'])
                    ) +
                    calculate_haversine_distance(
                        (locations[best_route[i]]['latitude'], locations[best_route[i]]['longitude']),
                        (locations[best_route[j+1]]['latitude'], locations[best_route[j+1]]['longitude'])
                    )
                )
                
                if new_dist < old_dist:
                    best_route = two_opt_swap(best_route, i, j)
                    improved = True
    
    return best_route

def optimize_delivery_route(locations: List[Dict], use_google_maps: bool = True) -> List[Dict]:
    """
    Optimize the delivery route using a combination of algorithms.
    Each location should be a dictionary with 'id', 'latitude', and 'longitude' keys.
    Returns the optimized route as a list of locations.
    """
    if not locations:
        return []
    
    # First, get an initial route using Nearest Neighbor
    initial_route = nearest_neighbor(locations)
    
    # Improve the route using 2-opt
    optimized_route_indices = two_opt(locations, initial_route)
    
    # Convert indices back to location dictionaries
    return [locations[idx] for idx in optimized_route_indices]

class RouteOptimizer:
    def __init__(self, locations: List[Dict]):
        """
        Initialize the route optimizer with a list of locations.
        Each location should be a dict with: id, latitude, longitude, address
        """
        self.locations = locations
        self.distances = {}  # Cache for distances between points
        self.times = {}      # Cache for travel times between points
        self._calculate_distances()

    def _get_google_maps_distance(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Tuple[float, float]:
        """
        Get the actual road distance and time between two points using Google Maps Distance Matrix API.
        Returns a tuple of (distance in km, time in hours).
        """
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            raise ValueError("Google Maps API key not found in environment variables")

        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': f"{origin[0]},{origin[1]}",
            'destinations': f"{destination[0]},{destination[1]}",
            'key': api_key,
            'mode': 'driving',
            'traffic_model': 'best_guess',
            'departure_time': 'now'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
                distance_km = data['rows'][0]['elements'][0]['distance']['value'] / 1000  # Convert meters to km
                duration_hrs = data['rows'][0]['elements'][0]['duration_in_traffic']['value'] / 3600  # Convert seconds to hours
                return distance_km, duration_hrs
            else:
                # Fallback to Haversine if API fails
                return self._calculate_haversine_distance(origin, destination)
        except Exception as e:
            print(f"Error using Google Maps API: {e}")
            # Fallback to Haversine if API fails
            return self._calculate_haversine_distance(origin, destination)

    def _calculate_haversine_distance(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calculate the distance between two points using the Haversine formula.
        Returns a tuple of (distance in km, estimated time in hours).
        """
        lat1, lon1 = origin
        lat2, lon2 = destination
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        R = 6371  # Earth's radius in kilometers
        
        distance = R * c
        
        # Estimate time based on average city speed (20 km/h)
        time = distance / 20
        
        return distance, time

    def _calculate_distances(self):
        """Calculate and cache distances and times between all pairs of locations."""
        for i, loc1 in enumerate(self.locations):
            for j, loc2 in enumerate(self.locations[i+1:], i+1):
                origin = (float(loc1['latitude']), float(loc1['longitude']))
                destination = (float(loc2['latitude']), float(loc2['longitude']))
                
                distance, time = self._get_google_maps_distance(origin, destination)
                
                # Cache both distance and time
                self.distances[(loc1['id'], loc2['id'])] = distance
                self.distances[(loc2['id'], loc1['id'])] = distance
                self.times[(loc1['id'], loc2['id'])] = time
                self.times[(loc2['id'], loc1['id'])] = time

    def get_distance(self, location1_id: int, location2_id: int) -> float:
        """Get the distance between two locations by their IDs."""
        return self.distances.get((location1_id, location2_id), 0)

    def get_time(self, location1_id: int, location2_id: int) -> float:
        """Get the travel time between two locations by their IDs."""
        return self.times.get((location1_id, location2_id), 0)

    def nearest_neighbor(self, start_location_id: int) -> Tuple[List[Dict], float, float]:
        """
        Implement the Nearest Neighbor algorithm for route optimization.
        Returns a tuple of (ordered locations list, total distance, total time).
        """
        unvisited = [loc for loc in self.locations if loc['id'] != start_location_id]
        current = next(loc for loc in self.locations if loc['id'] == start_location_id)
        route = [current]
        total_distance = 0
        total_time = 0

        while unvisited:
            # Find the nearest unvisited location
            nearest = min(unvisited, 
                        key=lambda x: self.get_distance(current['id'], x['id']))
            
            # Add to route and update total distance and time
            total_distance += self.get_distance(current['id'], nearest['id'])
            total_time += self.get_time(current['id'], nearest['id'])
            route.append(nearest)
            current = nearest
            unvisited.remove(nearest)

        return route, total_distance, total_time

    def optimize_route(self, start_location_id: int, algorithm: str = 'nearest_neighbor') -> Dict:
        """
        Optimize the delivery route using the specified algorithm.
        Returns a dictionary with the optimized route information.
        """
        if algorithm == 'nearest_neighbor':
            route, total_distance, total_time = self.nearest_neighbor(start_location_id)
        else:
            # Default to nearest neighbor if algorithm not implemented
            route, total_distance, total_time = self.nearest_neighbor(start_location_id)

        # Add time for stops:
        # - 3 minutes for each stop in between
        # - 5 minutes for loading at start
        # - 5 minutes for unloading at end
        num_stops = len(route) - 1  # Exclude starting point
        stop_time = (num_stops * 3 + 10) / 60  # Convert minutes to hours
        
        # Total time including stops
        total_time += stop_time
        
        # Convert to hours and minutes
        hours = int(total_time)
        minutes = int((total_time - hours) * 60)
        
        return {
            'locations': route,
            'total_distance': round(total_distance, 2),
            'estimated_time': f"{hours}h {minutes}m",
            'algorithm_used': algorithm,
            'num_stops': num_stops
        } 