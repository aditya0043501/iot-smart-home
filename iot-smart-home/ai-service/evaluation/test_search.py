"""
AETHER Classical AI Layer — Graph Search & Routing Unit Tests
--------------------------------------------------------------
Tests BFS, DFS, UCS, Greedy, and A* on emergency evacuation
and vacuum coverage planning.
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classical.search.routing import SearchComparisonEngine


def test_search_optimality():
    print("[TEST 1] Testing Search Optimality (A* and UCS must find the true shortest path)...")
    engine = SearchComparisonEngine()

    res = engine.compare_all(start="R7")
    comp = {r["algorithm"]: r for r in res["comparison"]}

    assert comp["A*"]["is_optimal_cost"], "A* must find optimal cost!"
    assert comp["UCS"]["is_optimal_cost"], "UCS must find optimal cost!"
    assert comp["A*"]["total_distance_meters"] == comp["UCS"]["total_distance_meters"]
    print(f"  ✓ Optimality confirmed: Shortest evacuation path is {comp['A*']['total_distance_meters']}m.")


def test_hazard_detour_routing():
    print("[TEST 2] Testing Emergency Detour Routing with Hazard Blockage...")
    engine = SearchComparisonEngine()

    # Block R2 (Living room)
    res = engine.compare_all(start="R3", blocked_rooms=["R2"])
    comp = {r["algorithm"]: r for r in res["comparison"]}

    # Path from R3 must exit through R5 (Backyard), avoiding blocked R2
    for algo in ["BFS", "UCS", "A*"]:
        path = comp[algo]["path"]
        assert "R2" not in path, f"{algo} routed through blocked room R2!"
        assert path == ["R3", "R5"], f"{algo} expected ['R3', 'R5'], got {path}"
    print("  ✓ Hazard avoidance confirmed: Clean detour found avoiding fire room.")


def test_vacuum_coverage_tour():
    print("[TEST 3] Testing Robot Vacuum Full-Coverage Tour...")
    engine = SearchComparisonEngine()
    vac = engine.compute_vacuum_coverage(start="R1")

    assert vac["rooms_covered"] == 8, "Vacuum must cover all 8 villa rooms"
    assert vac["total_coverage_distance"] > 0
    # Every room ID must appear in the tour
    all_rooms = {"R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"}
    assert all_rooms.issubset(set(vac["tour"])), "Tour must visit every single room in the house"
    print(f"  ✓ Full coverage tour generated: {vac['total_coverage_distance']}m across {vac['rooms_covered']} rooms.")


if __name__ == "__main__":
    print("==================================================")
    print(" RUNNING AETHER SEARCH & ROUTING UNIT TESTS")
    print("==================================================")
    test_search_optimality()
    test_hazard_detour_routing()
    test_vacuum_coverage_tour()
    print("==================================================")
    print(" ALL SEARCH TESTS PASSED SUCCESSFULLY! (3/3)")
    print("==================================================")
