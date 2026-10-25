"""
AETHER Classical AI Layer — Graph Search & Evacuation Routing
-------------------------------------------------------------
Side-by-side comparison of 5 classical search algorithms:
  1. Breadth-First Search (BFS)
  2. Depth-First Search (DFS)
  3. Uniform-Cost Search (UCS / Dijkstra)
  4. Greedy Best-First Search (GBFS)
  5. A* Search (A-Star with Admissible Euclidean / Manhattan Heuristic)

Operates on the canonical AETHER house topology graph for:
  - Fastest Emergency Evacuation Routing (with dynamic hazard blockage)
  - Complete Robot Vacuum Coverage Touring
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from collections import deque
import heapq
import time

from classical.graph.house_graph import house_graph, HouseGraph


class SearchResult:
    """Summary metrics of a search algorithm run."""

    def __init__(
        self,
        algorithm: str,
        path: List[str],
        cost: float,
        nodes_expanded: int,
        max_frontier_size: int,
        execution_time_us: float,
        trace: List[dict]
    ):
        self.algorithm = algorithm
        self.path = path
        self.cost = cost
        self.nodes_expanded = nodes_expanded
        self.max_frontier_size = max_frontier_size
        self.execution_time_us = execution_time_us
        self.trace = trace

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "path": self.path,
            "path_names": [house_graph.nodes[r].name for r in self.path] if self.path else [],
            "path_length_rooms": len(self.path),
            "total_distance_meters": round(self.cost, 2),
            "nodes_expanded": self.nodes_expanded,
            "max_frontier_size": self.max_frontier_size,
            "execution_time_microseconds": round(self.execution_time_us, 2),
            "trace": self.trace
        }


class SearchComparisonEngine:
    """Runs and benchmarks BFS, DFS, UCS, Greedy, and A* on the same routing task."""

    def __init__(self, graph: Optional[HouseGraph] = None):
        self.graph = graph or house_graph

    def _get_heuristic(self, node: str, goals: Set[str], heuristic_type: str = "euclidean") -> float:
        """Admissible heuristic: minimum distance from node to any goal room."""
        if not goals:
            return 0.0
        dist_fn = (
            self.graph.euclidean_distance
            if heuristic_type == "euclidean"
            else self.graph.manhattan_distance
        )
        return min(dist_fn(node, g) for g in goals)

    # ── 1. Breadth-First Search (BFS) ──────────────────────────
    def bfs(
        self,
        start: str,
        goals: Set[str],
        blocked_rooms: Set[str] = None
    ) -> SearchResult:
        t0 = time.perf_counter()
        blocked = blocked_rooms or set()

        frontier = deque([(start, [start], 0.0)])
        explored: Set[str] = set()
        trace = []
        step = 0
        max_frontier = 1

        while frontier:
            max_frontier = max(max_frontier, len(frontier))
            curr, path, cost = frontier.popleft()
            step += 1

            trace.append({
                "step": step,
                "current": curr,
                "path": path,
                "cost": round(cost, 2),
                "frontier": [item[0] for item in frontier],
                "explored": list(explored)
            })

            if curr in goals:
                dt_us = (time.perf_counter() - t0) * 1e6
                return SearchResult("BFS", path, cost, step, max_frontier, dt_us, trace)

            if curr not in explored:
                explored.add(curr)
                for nbr in self.graph.get_neighbors(curr, only_passable=True):
                    if nbr not in explored and nbr not in blocked and not any(item[0] == nbr for item in frontier):
                        edge = self.graph.get_edge(curr, nbr)
                        edge_dist = edge.distance if edge else 1.0
                        frontier.append((nbr, path + [nbr], cost + edge_dist))

        dt_us = (time.perf_counter() - t0) * 1e6
        return SearchResult("BFS", [], float("inf"), step, max_frontier, dt_us, trace)

    # ── 2. Depth-First Search (DFS) ────────────────────────────
    def dfs(
        self,
        start: str,
        goals: Set[str],
        blocked_rooms: Set[str] = None
    ) -> SearchResult:
        t0 = time.perf_counter()
        blocked = blocked_rooms or set()

        frontier = [(start, [start], 0.0)]
        explored: Set[str] = set()
        trace = []
        step = 0
        max_frontier = 1

        while frontier:
            max_frontier = max(max_frontier, len(frontier))
            curr, path, cost = frontier.pop()  # LIFO stack
            step += 1

            trace.append({
                "step": step,
                "current": curr,
                "path": path,
                "cost": round(cost, 2),
                "frontier": [item[0] for item in frontier],
                "explored": list(explored)
            })

            if curr in goals:
                dt_us = (time.perf_counter() - t0) * 1e6
                return SearchResult("DFS", path, cost, step, max_frontier, dt_us, trace)

            if curr not in explored:
                explored.add(curr)
                for nbr in reversed(self.graph.get_neighbors(curr, only_passable=True)):
                    if nbr not in explored and nbr not in blocked:
                        edge = self.graph.get_edge(curr, nbr)
                        edge_dist = edge.distance if edge else 1.0
                        frontier.append((nbr, path + [nbr], cost + edge_dist))

        dt_us = (time.perf_counter() - t0) * 1e6
        return SearchResult("DFS", [], float("inf"), step, max_frontier, dt_us, trace)

    # ── 3. Uniform-Cost Search (UCS) ───────────────────────────
    def ucs(
        self,
        start: str,
        goals: Set[str],
        blocked_rooms: Set[str] = None
    ) -> SearchResult:
        t0 = time.perf_counter()
        blocked = blocked_rooms or set()

        # (cost, counter, curr, path)
        frontier = []
        counter = 0
        heapq.heappush(frontier, (0.0, counter, start, [start]))
        best_g: Dict[str, float] = {start: 0.0}
        explored: Set[str] = set()
        trace = []
        step = 0
        max_frontier = 1

        while frontier:
            max_frontier = max(max_frontier, len(frontier))
            cost, _, curr, path = heapq.heappop(frontier)
            step += 1

            trace.append({
                "step": step,
                "current": curr,
                "path": path,
                "cost": round(cost, 2),
                "frontier": [item[2] for item in frontier],
                "explored": list(explored)
            })

            if curr in goals:
                dt_us = (time.perf_counter() - t0) * 1e6
                return SearchResult("UCS", path, cost, step, max_frontier, dt_us, trace)

            if curr not in explored:
                explored.add(curr)
                for nbr in self.graph.get_neighbors(curr, only_passable=True):
                    if nbr not in blocked:
                        edge = self.graph.get_edge(curr, nbr)
                        new_g = cost + (edge.distance if edge else 1.0)
                        if new_g < best_g.get(nbr, float("inf")):
                            best_g[nbr] = new_g
                            counter += 1
                            heapq.heappush(frontier, (new_g, counter, nbr, path + [nbr]))

        dt_us = (time.perf_counter() - t0) * 1e6
        return SearchResult("UCS", [], float("inf"), step, max_frontier, dt_us, trace)

    # ── 4. Greedy Best-First Search ────────────────────────────
    def greedy(
        self,
        start: str,
        goals: Set[str],
        blocked_rooms: Set[str] = None,
        heuristic_type: str = "euclidean"
    ) -> SearchResult:
        t0 = time.perf_counter()
        blocked = blocked_rooms or set()

        h0 = self._get_heuristic(start, goals, heuristic_type)
        frontier = []
        counter = 0
        heapq.heappush(frontier, (h0, 0.0, counter, start, [start]))
        explored: Set[str] = set()
        trace = []
        step = 0
        max_frontier = 1

        while frontier:
            max_frontier = max(max_frontier, len(frontier))
            h_val, cost, _, curr, path = heapq.heappop(frontier)
            step += 1

            trace.append({
                "step": step,
                "current": curr,
                "path": path,
                "heuristic": round(h_val, 2),
                "cost": round(cost, 2),
                "frontier": [item[3] for item in frontier],
                "explored": list(explored)
            })

            if curr in goals:
                dt_us = (time.perf_counter() - t0) * 1e6
                return SearchResult("Greedy", path, cost, step, max_frontier, dt_us, trace)

            if curr not in explored:
                explored.add(curr)
                for nbr in self.graph.get_neighbors(curr, only_passable=True):
                    if nbr not in explored and nbr not in blocked:
                        edge = self.graph.get_edge(curr, nbr)
                        edge_dist = edge.distance if edge else 1.0
                        h_nbr = self._get_heuristic(nbr, goals, heuristic_type)
                        counter += 1
                        heapq.heappush(frontier, (h_nbr, cost + edge_dist, counter, nbr, path + [nbr]))

        dt_us = (time.perf_counter() - t0) * 1e6
        return SearchResult("Greedy", [], float("inf"), step, max_frontier, dt_us, trace)

    # ── 5. A* Search ───────────────────────────────────────────
    def astar(
        self,
        start: str,
        goals: Set[str],
        blocked_rooms: Set[str] = None,
        heuristic_type: str = "euclidean"
    ) -> SearchResult:
        t0 = time.perf_counter()
        blocked = blocked_rooms or set()

        h0 = self._get_heuristic(start, goals, heuristic_type)
        frontier = []
        counter = 0
        # (f_score, g_score, counter, node, path)
        heapq.heappush(frontier, (h0, 0.0, counter, start, [start]))
        best_g: Dict[str, float] = {start: 0.0}
        explored: Set[str] = set()
        trace = []
        step = 0
        max_frontier = 1

        while frontier:
            max_frontier = max(max_frontier, len(frontier))
            f_score, g_cost, _, curr, path = heapq.heappop(frontier)
            step += 1

            trace.append({
                "step": step,
                "current": curr,
                "path": path,
                "f_score": round(f_score, 2),
                "g_cost": round(g_cost, 2),
                "heuristic": round(f_score - g_cost, 2),
                "frontier": [item[3] for item in frontier],
                "explored": list(explored)
            })

            if curr in goals:
                dt_us = (time.perf_counter() - t0) * 1e6
                return SearchResult("A*", path, g_cost, step, max_frontier, dt_us, trace)

            if curr not in explored:
                explored.add(curr)
                for nbr in self.graph.get_neighbors(curr, only_passable=True):
                    if nbr not in blocked:
                        edge = self.graph.get_edge(curr, nbr)
                        edge_dist = edge.distance if edge else 1.0
                        new_g = g_cost + edge_dist

                        if new_g < best_g.get(nbr, float("inf")):
                            best_g[nbr] = new_g
                            h = self._get_heuristic(nbr, goals, heuristic_type)
                            counter += 1
                            heapq.heappush(frontier, (new_g + h, new_g, counter, nbr, path + [nbr]))

        dt_us = (time.perf_counter() - t0) * 1e6
        return SearchResult("A*", [], float("inf"), step, max_frontier, dt_us, trace)

    def compare_all(
        self,
        start: str = "R7",
        goals: Optional[List[str]] = None,
        blocked_rooms: Optional[List[str]] = None,
        heuristic_type: str = "euclidean"
    ) -> Dict[str, Any]:
        """
        Runs all 5 algorithms on identical problem parameters.
        Returns side-by-side comparison matrix with winner highlights.
        """
        goal_set = set(goals) if goals else set(self.graph.get_exits())
        blocked_set = set(blocked_rooms) if blocked_rooms else set()

        results = [
            self.bfs(start, goal_set, blocked_set),
            self.dfs(start, goal_set, blocked_set),
            self.ucs(start, goal_set, blocked_set),
            self.greedy(start, goal_set, blocked_set, heuristic_type),
            self.astar(start, goal_set, blocked_set, heuristic_type),
        ]

        # Find optimal cost
        valid_costs = [r.cost for r in results if r.path]
        min_cost = min(valid_costs) if valid_costs else float("inf")
        min_expansions = min(r.nodes_expanded for r in results if r.path)

        comparison_table = []
        for r in results:
            d = r.to_dict()
            d["is_optimal_cost"] = abs(r.cost - min_cost) < 1e-4 if r.path else False
            d["is_minimal_expansions"] = r.nodes_expanded == min_expansions if r.path else False
            comparison_table.append(d)

        return {
            "start_room": start,
            "start_room_name": self.graph.nodes[start].name,
            "target_goals": sorted(list(goal_set)),
            "blocked_rooms": sorted(list(blocked_set)),
            "heuristic_used": heuristic_type,
            "comparison": comparison_table,
            "summary": {
                "fastest_path_meters": round(min_cost, 2),
                "optimal_algorithm": "A* / UCS",
                "least_expansions": min_expansions
            }
        }

    def compute_vacuum_coverage(self, start: str = "R1") -> Dict[str, Any]:
        """
        Generates full-coverage tour across all villa rooms using greedy nearest-neighbor TSP.
        Simulates autonomous robot vacuum path planning.
        """
        unvisited = set(self.graph.nodes.keys()) - {start}
        current = start
        tour = [start]
        total_distance = 0.0
        legs = []

        while unvisited:
            # Find closest unvisited room using A*
            best_nbr = None
            best_cost = float("inf")
            best_path = []

            for candidate in sorted(unvisited):
                res = self.astar(current, {candidate})
                if res.cost < best_cost:
                    best_cost = res.cost
                    best_nbr = candidate
                    best_path = res.path

            if not best_nbr:
                break

            unvisited.remove(best_nbr)
            total_distance += best_cost
            legs.append({
                "from": current,
                "to": best_nbr,
                "leg_path": best_path,
                "distance_meters": round(best_cost, 2)
            })
            current = best_nbr
            tour.extend(best_path[1:])

        return {
            "start_room": start,
            "total_coverage_distance": round(total_distance, 2),
            "rooms_covered": len(self.graph.nodes),
            "tour": tour,
            "legs": legs
        }
