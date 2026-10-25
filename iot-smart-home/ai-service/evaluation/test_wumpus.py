"""
AETHER Classical AI Layer — Wumpus Agent Evaluation & Unit Tests
----------------------------------------------------------------
Tests Propositional Logic Knowledge Base, TT-Entails Model Checking,
and Autonomous Safe Patrol on the Canonical Villa Topology.
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classical.graph.house_graph import house_graph
from classical.logic.wumpus import (
    WumpusHazardAgent,
    LogicalPercept,
    PropositionalKB,
    simulate_hazard_scenario,
    diagnose_smart_home_sensors,
    HAZARDS
)


def test_house_graph_topology():
    print("[TEST 1] House Graph Topology...")
    assert len(house_graph.nodes) == 8, f"Expected 8 rooms, found {len(house_graph.nodes)}"
    assert len(house_graph.edges) == 8, f"Expected 8 edges, found {len(house_graph.edges)}"

    # Check emergency exits
    exits = house_graph.get_exits()
    assert "R1" in exits, "R1 must be an exit"
    assert "R4" in exits, "R4 must be an exit"
    assert "R5" in exits, "R5 must be an exit"

    # Check distances
    e_1_2 = house_graph.get_edge("R1", "R2")
    assert e_1_2 is not None and e_1_2.distance == 3.5
    print("  ✓ Graph topology passed (8 rooms, 8 edges, 3 emergency exits).")


def test_propositional_model_checking():
    print("[TEST 2] Propositional Logic & TT-Entails Model Checking...")
    kb = PropositionalKB("FIRE")

    # Start: R1 has no smoke
    kb.tell_percept("R1", False)
    # R1 entered and safe
    kb.tell_hazard_absence("R1")

    # R1 has neighbors R2, R4. Since SMOKE_R1 is false, R2 and R4 cannot contain fire!
    entailed_r2_safe, reason_r2, _, _ = kb.entails("FIRE_R2", query_value=False)
    entailed_r4_safe, reason_r4, _, _ = kb.entails("FIRE_R4", query_value=False)

    assert entailed_r2_safe, "FIRE_R2 must be proven absent (safe)"
    assert entailed_r4_safe, "FIRE_R4 must be proven absent (safe)"

    # Now observe SMOKE at R2
    kb.tell_percept("R2", True)

    # Neighbors of R2: R1, R3, R4, R6. Since R1, R2, R4 are clear, fire must be in R3 or R6.
    # At this point, R3 alone is indeterminate
    entailed_r3_danger, _, sat_r3, tot_r3 = kb.entails("FIRE_R3", query_value=True)
    assert not entailed_r3_danger, "FIRE_R3 should still be indeterminate (could be R6)"

    # Now observe NO SMOKE at R6
    kb.tell_percept("R6", False)

    # Now FIRE_R3 MUST be proven DANGEROUS!
    entailed_r3_confirmed, reason_r3, sat_c, tot_c = kb.entails("FIRE_R3", query_value=True)
    assert entailed_r3_confirmed, f"FIRE_R3 must be proven present! Reason: {reason_r3}"
    assert sat_c == tot_c, "Must hold in 100% of consistent models"
    print(f"  ✓ Model checking passed: Deductions proved across all {tot_c} models.")


def test_autonomous_patrol_simulation():
    print("[TEST 3] Autonomous Patrol Simulation...")
    trace = simulate_hazard_scenario(
        hazard_location="R3",
        hazard_type="FIRE",
        static_sensor_rooms=["R6", "R5"]
    )

    assert len(trace) > 0, "Trace cannot be empty"
    # Agent must never enter R3 (the hazardous room)
    visited_rooms = trace[-1]["visited_rooms"]
    assert "R3" not in visited_rooms, "Robot violated safety rule: entered hazardous room R3!"
    assert "R1" in visited_rooms, "Robot must visit R1"

    # Confirmed hazard at end must be R3
    final_hazards = trace[-1]["confirmed_hazards"]
    assert "R3" in final_hazards, f"Expected R3 hazard confirmed, got {final_hazards}"
    assert "FIRE" in final_hazards["R3"], "Hazard type must be FIRE"
    print(f"  ✓ Patrol simulation passed: Explored {len(visited_rooms)} safe rooms, successfully isolated hazard at R3.")


def test_stationary_sensor_diagnosis():
    print("[TEST 4] Whole-Home Stationary Sensor Diagnosis...")
    # Fire in Kitchen (R3) triggers smoke in R3, R2, R5
    readings = {
        "R1": {"smoke": False, "stench": False},
        "R2": {"smoke": True,  "stench": False},
        "R4": {"smoke": False, "stench": False},
        "R5": {"smoke": True,  "stench": False},
        "R6": {"smoke": False, "stench": False},
    }
    diagnosis = diagnose_smart_home_sensors(readings)
    hazards = diagnosis["confirmed_hazards"]
    assert "R3" in hazards and "FIRE" in hazards["R3"], f"Diagnostic failed: {hazards}"
    assert diagnosis["room_evaluations"]["R3"]["status"] == "DANGEROUS"
    assert diagnosis["room_evaluations"]["R1"]["status"] == "SAFE"
    print("  ✓ Sensor diagnosis passed: Pinpointed Kitchen Fire with certainty.")


if __name__ == "__main__":
    print("==================================================")
    print(" RUNNING AETHER WUMPUS AGENT UNIT TESTS")
    print("==================================================")
    test_house_graph_topology()
    test_propositional_model_checking()
    test_autonomous_patrol_simulation()
    test_stationary_sensor_diagnosis()
    print("==================================================")
    print(" ALL TESTS PASSED SUCCESSFULLY! (4/4)")
    print("==================================================")
