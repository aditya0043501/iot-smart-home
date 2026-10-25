"""
AETHER Classical AI Layer — Optimization Algorithms Unit Tests
---------------------------------------------------------------
Tests Hill Climbing, Simulated Annealing, and Genetic Algorithm
on energy-cost load shifting under dynamic TOU tariffs.
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classical.optimization.energy_opt import OptimizerEngine


def test_optimization_cost_reduction():
    print("[TEST 1] Testing Optimization Cost Reduction...")
    engine = OptimizerEngine()
    # Baseline with expensive peak daytime schedule
    seed = [10, 11, 12, 19, 18]
    res = engine.compare_all(seed_schedule=seed)

    base_cost = res["unoptimized_baseline"]["total_cost_inr"]

    for comp in res["comparison"]:
        final_cost = comp["final_cost_inr"]
        assert final_cost < base_cost, f"{comp['algorithm']} failed to reduce cost! {final_cost} >= {base_cost}"
        assert comp["savings_percent"] > 0.0, "Savings percentage must be positive"
        print(f"  ✓ {comp['algorithm']}: Cost reduced from ₹{base_cost} to ₹{final_cost} ({comp['savings_percent']}% savings).")


def test_convergence_histories_present():
    print("[TEST 2] Testing Convergence Curve Data Integrity...")
    engine = OptimizerEngine()
    res = engine.compare_all()

    curves = res["convergence_curves"]
    assert "hill_climbing" in curves, "Must contain hill climbing curve"
    assert "simulated_annealing" in curves, "Must contain simulated annealing curve"
    assert "genetic_algorithm" in curves, "Must contain genetic algorithm curve"

    assert len(curves["hill_climbing"]) > 1
    assert len(curves["simulated_annealing"]) == 101  # 0 to 100 iterations
    assert len(curves["genetic_algorithm"]) == 61    # 0 to 60 generations
    print("  ✓ Synchronized convergence history vectors generated successfully.")


if __name__ == "__main__":
    print("==================================================")
    print(" RUNNING AETHER OPTIMIZATION ALGORITHMS TESTS")
    print("==================================================")
    test_optimization_cost_reduction()
    test_convergence_histories_present()
    print("==================================================")
    print(" ALL OPTIMIZATION TESTS PASSED! (2/2)")
    print("==================================================")
