"""
AETHER Classical AI Layer — CSP Appliance Scheduler Unit Tests
---------------------------------------------------------------
Tests AC-3 Arc Consistency, MRV, Backtracking with Forward Checking,
and Peak Power Cap Enforcement.
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classical.csp.scheduler import ApplianceCSPSolver, get_default_appliances


def test_csp_power_cap_compliance():
    print("[TEST 1] Testing Power Cap Compliance...")
    cap = 3500.0
    solver = ApplianceCSPSolver(power_cap_watts=cap, total_horizon_slots=12)
    sol = solver.solve(use_ac3=True)

    assert sol["success"] is True, "CSP Solver should find a valid schedule at 3500W"
    profile = sol["hourly_load_profile"]

    for h in profile:
        load = h["total_watts"]
        assert load <= cap + 1e-4, f"Power cap exceeded at {h['hour']}: {load}W > {cap}W"

    peak = sol["solver_metrics"]["peak_power_watts"]
    assert peak <= cap, f"Peak power {peak}W exceeds cap {cap}W"
    print(f"  ✓ Power cap compliance verified: Peak load {peak}W <= {cap}W.")


def test_heavy_load_mutex_constraint():
    print("[TEST 2] Testing Heavy Load Mutex Constraint (No two heavy loads at once)...")
    solver = ApplianceCSPSolver(power_cap_watts=3500.0)
    sol = solver.solve(use_ac3=True)
    sched = sol["schedule"]

    heavy_apps = [name for name, app in solver.appliances.items() if app.is_heavy_load]

    # Verify no two heavy appliances share any active time slot
    for i in range(len(heavy_apps)):
        for j in range(i + 1, len(heavy_apps)):
            a1, a2 = heavy_apps[i], heavy_apps[j]
            s1, e1 = sched[a1]["start_slot"], sched[a1]["end_slot"]
            s2, e2 = sched[a2]["start_slot"], sched[a2]["end_slot"]

            overlap = max(s1, s2) < min(e1, e2)
            assert not overlap, f"Heavy load mutex violation: {a1} [{s1}-{e1}] and {a2} [{s2}-{e2}] overlap!"

    print(f"  ✓ Mutex constraint verified: All {len(heavy_apps)} heavy loads scheduled in disjoint time slots.")


def test_overconstrained_unsolvable_detection():
    print("[TEST 3] Testing Overconstrained Failure Detection (Power Cap too low)...")
    # Setting an impossibly low power cap of 1500W (when EV Charger alone requires 2800W)
    solver = ApplianceCSPSolver(power_cap_watts=1500.0)
    sol = solver.solve(use_ac3=True)

    assert sol["success"] is False, "Solver must detect that 1500W cannot run a 2800W EV charger"
    print("  ✓ Correctly rejected unsolvable constraints.")


if __name__ == "__main__":
    print("==================================================")
    print(" RUNNING AETHER CSP SCHEDULER UNIT TESTS")
    print("==================================================")
    test_csp_power_cap_compliance()
    test_heavy_load_mutex_constraint()
    test_overconstrained_unsolvable_detection()
    print("==================================================")
    print(" ALL CSP TESTS PASSED SUCCESSFULLY! (3/3)")
    print("==================================================")
