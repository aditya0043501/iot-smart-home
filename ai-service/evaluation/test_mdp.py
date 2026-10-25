"""
AETHER Classical AI Layer — MDP Value Iteration Unit Tests
----------------------------------------------------------
Tests Bellman Value Iteration convergence, optimal thermostat policy,
and trade-off between occupant comfort and energy cost.
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classical.probabilistic.mdp_thermostat import ThermostatMDP


def test_value_iteration_convergence():
    print("[TEST 1] Testing Value Iteration Convergence...")
    mdp = ThermostatMDP(gamma=0.90, epsilon=0.001)
    res = mdp.value_iteration()

    assert res["converged"] is True, "Value iteration must converge"
    assert res["total_iterations"] < 150, "Should converge within 150 iterations"
    assert len(res["convergence_history"]) == res["total_iterations"]
    deltas = [h["delta"] for h in res["convergence_history"]]
    assert deltas[-1] < 0.001, "Final delta must be below epsilon"
    print(f"  ✓ Value iteration converged in {res['total_iterations']} steps (Final delta: {deltas[-1]}).")


def test_optimal_policy_rationality():
    print("[TEST 2] Testing Rationality of Learned Thermostat Policy...")
    mdp = ThermostatMDP()
    res = mdp.value_iteration()
    policy = res["optimal_policy"]

    # When Hot and Occupied, optimal action must be Cool
    assert policy["Hot_Occupied"]["optimal_action"] == "Cool", "Hot & Occupied must trigger Cool"
    # When VeryCold and Occupied, optimal action must be Heat
    assert policy["VeryCold_Occupied"]["optimal_action"] == "Heat", "VeryCold & Occupied must trigger Heat"
    # When Comfortable and Occupied, optimal action should be Off (saving power)
    assert policy["Comfortable_Occupied"]["optimal_action"] == "Off", "Comfortable state should turn AC Off"
    print("  ✓ Rational control actions confirmed for all core climate states.")


if __name__ == "__main__":
    print("==================================================")
    print(" RUNNING AETHER MDP VALUE ITERATION UNIT TESTS")
    print("==================================================")
    test_value_iteration_convergence()
    test_optimal_policy_rationality()
    print("==================================================")
    print(" ALL MDP TESTS PASSED SUCCESSFULLY! (2/2)")
    print("==================================================")
