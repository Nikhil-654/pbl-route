from typing import Dict, List, Set, Tuple
import math

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

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in kilometers
    
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
        # Find the vertex with the minimum distance
        current = min(unvisited, key=lambda x: distances[x])
        
        if distances[current] == float('infinity'):
            break
            
        unvisited.remove(current)
        
        # Update distances to neighbors
        for neighbor in graph.get_neighbors(current):
            if neighbor in unvisited:
                distance = distances[current] + graph.get_distance(current, neighbor)
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
    
    return distances, previous

def get_shortest_path(previous: Dict[str, str], start: str, end: str) -> List[str]:
    """
    Reconstruct the shortest path from start to end using the previous vertices.
    """
    path = []
    current = end
    
    while current is not None:
        path.append(current)
        current = previous[current]
    
    path.reverse()
    return path if path[0] == start else []

def optimize_delivery_route(locations: List[Dict]) -> List[Dict]:
    """
    Optimize the delivery route for a list of locations.
    Each location should be a dictionary with 'id', 'latitude', and 'longitude' keys.
    Returns the optimized route as a list of locations.
    """
    # Create a graph from the locations
    graph = Graph()
    
    # Add edges between all locations
    for i, loc1 in enumerate(locations):
        for j, loc2 in enumerate(locations[i+1:], i+1):
            distance = calculate_distance(
                loc1['latitude'], loc1['longitude'],
                loc2['latitude'], loc2['longitude']
            )
            graph.add_edge(loc1['id'], loc2['id'], distance)
    
    # Find the optimal route starting from the first location
    start = locations[0]['id']
    distances, previous = dijkstra(graph, start)
    
    # Reconstruct the path
    path = []
    current = start
    unvisited = set(loc['id'] for loc in locations[1:])
    
    while unvisited:
        next_stop = min(unvisited, key=lambda x: distances[x])
        path.extend(get_shortest_path(previous, current, next_stop)[1:])
        current = next_stop
        unvisited.remove(next_stop)
    
    # Convert path IDs back to location dictionaries
    id_to_location = {loc['id']: loc for loc in locations}
    return [id_to_location[loc_id] for loc_id in path] 