"""
AETHER Classical AI Layer — STRIPS Planner Unit Tests
-----------------------------------------------------
Tests forward state-space progression search, precondition satisfaction,
and dynamic replanning when a smart home device goes offline.
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classical.planning.strips import (
    STRIPSPlanner,
    PRESET_GOALS,
    get_default_initial_state
)


def test_preset_plans():
    print("[TEST 1] Testing Canonical Preset Smart Home Plans...")
    planner = STRIPSPlanner()
    s0 = get_default_initial_state()

    for key in ["movie_night", "leave_home", "sleep_mode", "morning_routine"]:
        info = PRESET_GOALS[key]
        res = planner.solve(s0, info["goal_predicates"])
        assert res["success"] is True, f"Plan failed for {key}"
        assert res["plan_length"] > 0, f"Plan length must be > 0 for {key}"
        print(f"  ✓ {info['title']}: {res['plan_length']} actions, {res['nodes_expanded']} nodes expanded.")


def test_precondition_chaining():
    print("[TEST 2] Testing Precondition Chaining (Cinema TV requires Curtains Closed)...")
    planner = STRIPSPlanner()
    s0 = get_default_initial_state()

    # In movie night, CurtainsClosed is a precondition for TurnOnCinemaDisplay
    res = planner.solve(s0, PRESET_GOALS["movie_night"]["goal_predicates"])
    action_names = [a["name"] for a in res["plan"]]

    assert "CloseMotorizedCurtains" in action_names, "Curtains must be closed"
    assert "TurnOnCinemaDisplay" in action_names, "TV must be turned on"

    curtain_idx = action_names.index("CloseMotorizedCurtains")
    tv_idx = action_names.index("TurnOnCinemaDisplay")
    assert curtain_idx < tv_idx, "CloseMotorizedCurtains MUST precede TurnOnCinemaDisplay!"
    print("  ✓ Precondition dependency satisfied: Curtains closed before TV power-on.")


def test_dynamic_replanning():
    print("[TEST 3] Testing Dynamic Replanning on Hardware Fault (dev-1 offline)...")
    planner = STRIPSPlanner()
    s0 = get_default_initial_state()

    replan = planner.replan_on_failure(
        s0,
        PRESET_GOALS["movie_night"]["goal_predicates"],
        failed_device_id="dev-1"
    )

    assert replan["replanning_success"] is True, "Replanning must find alternative solution"
    orig_names = [a["name"] for a in replan["original_plan"]]
    replan_names = [a["name"] for a in replan["replanned_plan"]]

    assert "DimLivingLights" in orig_names, "Original plan used DimLivingLights"
    assert "DimLivingLights" not in replan_names, "Replanned plan must NOT use broken dev-1"
    assert "TurnOnAmbientAccentStrips" in replan_names, "Replanned plan must use fallback accent lighting"
    print("  ✓ Replanning successfully adapted around broken hardware.")


if __name__ == "__main__":
    print("==================================================")
    print(" RUNNING AETHER STRIPS PLANNER UNIT TESTS")
    print("==================================================")
    test_preset_plans()
    test_precondition_chaining()
    test_dynamic_replanning()
    print("==================================================")
    print(" ALL PLANNING TESTS PASSED SUCCESSFULLY! (3/3)")
    print("==================================================")
