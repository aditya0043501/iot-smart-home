"""
AETHER Classical AI Layer — House Topology Graph
-------------------------------------------------
Canonical spatial representation of the smart villa.
Shared across Search, Wumpus World, STRIPS Planning, and Evacuation Routing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class RoomNode:
    id: str                    # e.g. "R1"
    name: str                  # e.g. "Living Room"
    floor: int                 # 1 = Ground, 2 = Upstairs
    x: float                   # Coordinate in meters (for distance & visualization)
    y: float
    z: float                   # Height: 0 = Ground, 3.2 = Level 2
    devices: List[str]         # Device IDs located in this room
    is_exit: bool = False      # Emergency exit point to outdoors
    description: str = ""


@dataclass
class DoorEdge:
    room_a: str
    room_b: str
    distance: float            # Metric distance in meters
    door_type: str             # "open_archway", "standard_door", "sliding_glass", "stairs"
    is_passable: bool = True   # Can be blocked by fire, debris, or locked doors


class HouseGraph:
    """
    Undirected topological graph of the AETHER smart villa.
    Provides adjacency queries, Euclidean heuristics, and spatial lookups.
    """

    def __init__(self):
        self.nodes: Dict[str, RoomNode] = {}
        self.edges: List[DoorEdge] = []
        self._adj: Dict[str, Dict[str, DoorEdge]] = {}
        self._build_default_house()

    def _build_default_house(self):
        """Constructs the canonical 8-room villa model."""
        rooms = [
            RoomNode("R1", "Front Porch & Entrance", floor=1, x=0.0,  y=0.0,  z=0.0,
                     devices=["dev-3"], is_exit=True,
                     description="Front exterior porch with smart deadbolt lock."),
            RoomNode("R2", "Living Room Hub",        floor=1, x=0.0,  y=5.0,  z=0.0,
                     devices=["dev-1", "dev-2"], is_exit=False,
                     description="Central double-height living area with climate control and lighting."),
            RoomNode("R3", "Kitchen & Dining",       floor=1, x=6.0,  y=5.0,  z=0.0,
                     devices=["dev-6", "dev-8"], is_exit=False,
                     description="Kitchen space with smart coffee maker and high-power oven."),
            RoomNode("R4", "Garage & EV Carport",    floor=1, x=-6.0, y=5.0,  z=0.0,
                     devices=[], is_exit=True,
                     description="Automated vehicle bay with EV charging dock and driveway exit."),
            RoomNode("R5", "Backyard & Garden",      floor=1, x=6.0,  y=11.0, z=0.0,
                     devices=["dev-7"], is_exit=True,
                     description="Outdoor perimeter monitored by HD security camera."),
            RoomNode("R6", "Hallway & Stairwell",    floor=1, x=0.0,  y=9.0,  z=0.0,
                     devices=[], is_exit=False,
                     description="Transitional corridor providing staircase access to Level 2."),
            RoomNode("R7", "Master Bedroom",         floor=2, x=0.0,  y=9.0,  z=3.2,
                     devices=["dev-4", "dev-5"], is_exit=False,
                     description="Upstairs master suite with AeroFlow fan and ambient lighting."),
            RoomNode("R8", "Upper Balcony",          floor=2, x=0.0,  y=14.0, z=3.2,
                     devices=[], is_exit=False,
                     description="Second-story cantilevered balcony overlooking grounds."),
        ]

        for r in rooms:
            self.add_node(r)

        # Interconnected doorways and passageways
        connections = [
            ("R1", "R2", 3.5, "standard_door"),
            ("R2", "R3", 4.0, "open_archway"),
            ("R2", "R4", 4.5, "fire_door"),
            ("R2", "R6", 3.0, "open_archway"),
            ("R3", "R5", 3.5, "sliding_glass"),
            ("R4", "R1", 7.0, "exterior_driveway"),
            ("R6", "R7", 5.0, "stairs"),
            ("R7", "R8", 3.0, "sliding_glass"),
        ]

        for a, b, dist, dtype in connections:
            self.add_edge(a, b, dist, dtype)

    def add_node(self, node: RoomNode):
        self.nodes[node.id] = node
        if node.id not in self._adj:
            self._adj[node.id] = {}

    def add_edge(self, room_a: str, room_b: str, distance: float, door_type: str = "standard_door"):
        edge = DoorEdge(room_a, room_b, distance, door_type)
        self.edges.append(edge)
        self._adj.setdefault(room_a, {})[room_b] = edge
        self._adj.setdefault(room_b, {})[room_a] = edge

    def get_neighbors(self, room_id: str, only_passable: bool = True) -> List[str]:
        """Returns list of adjacent room IDs."""
        if room_id not in self._adj:
            return []
        neighbors = []
        for nbr, edge in self._adj[room_id].items():
            if only_passable and not edge.is_passable:
                continue
            neighbors.append(nbr)
        return sorted(neighbors)

    def get_edge(self, room_a: str, room_b: str) -> Optional[DoorEdge]:
        return self._adj.get(room_a, {}).get(room_b)

    def euclidean_distance(self, room_a: str, room_b: str) -> float:
        """3D Euclidean distance used as admissible heuristic for A*."""
        na = self.nodes.get(room_a)
        nb = self.nodes.get(room_b)
        if not na or not nb:
            return 0.0
        return ((na.x - nb.x)**2 + (na.y - nb.y)**2 + (na.z - nb.z)**2) ** 0.5

    def manhattan_distance(self, room_a: str, room_b: str) -> float:
        """Manhattan distance heuristic."""
        na = self.nodes.get(room_a)
        nb = self.nodes.get(room_b)
        if not na or not nb:
            return 0.0
        return abs(na.x - nb.x) + abs(na.y - nb.y) + abs(na.z - nb.z)

    def get_exits(self) -> List[str]:
        """Returns all emergency exit room IDs."""
        return [node.id for node in self.nodes.values() if node.is_exit]

    def to_dict(self) -> dict:
        """Serializes graph topology for UI visualization."""
        return {
            "rooms": [
                {
                    "id": r.id,
                    "name": r.name,
                    "floor": r.floor,
                    "x": r.x,
                    "y": r.y,
                    "z": r.z,
                    "devices": r.devices,
                    "is_exit": r.is_exit,
                    "description": r.description
                }
                for r in self.nodes.values()
            ],
            "connections": [
                {
                    "from": e.room_a,
                    "to": e.room_b,
                    "distance": e.distance,
                    "door_type": e.door_type,
                    "is_passable": e.is_passable
                }
                for e in self.edges
            ]
        }


# Global singleton house topology
house_graph = HouseGraph()
