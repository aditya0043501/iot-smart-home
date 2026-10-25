"""
AETHER Classical AI Layer — Expert System Unit Tests
----------------------------------------------------
Tests forward chaining (reactive data-driven alerts) and
backward chaining (diagnostic root-cause proof tree).
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classical.logic.expert_system import ExpertSystem


def test_forward_chaining():
    print("[TEST 1] Testing Forward Chaining...")
    es = ExpertSystem()

    # Scenario: Window left open with AC running
    fc = es.forward_chain({"WindowOpen", "ACOn"})
    inferred = set(fc["new_inferred_facts"])

    assert "EnergyWasteAlert" in inferred, "Rule R-ENERGY-01 must fire"
    assert "PlayEcoAudioChime" in inferred, "Cascading rule R-ENERGY-02 must fire"
    print(f"  ✓ Forward chaining passed: Inferred {len(inferred)} facts in {fc['total_rules_fired']} rule firings.")


def test_backward_chaining_explanation():
    print("[TEST 2] Testing Backward Chaining Root-Cause Proof Tree...")
    es = ExpertSystem()

    # Query: Why is SendSecurityDispatchAlert true?
    facts = {"MotionDetectedYard", "PerimeterArmed", "NoResidentPresent"}
    bc = es.backward_chain("SendSecurityDispatchAlert", facts)

    assert bc["proven"] is True, "Hypothesis must be proven from facts"
    assert "IntrusionAlarmTriggered" in str(bc["proof_tree"]), "Sub-goal must be satisfied via rule"
    assert len(bc["root_explanation"]) >= 3, "Explanation trace must cite rules and sensor facts"
    print("  ✓ Backward chaining passed: Full root-cause proof tree generated.")


def test_unproven_backward_query():
    print("[TEST 3] Testing Backward Chaining on Unproven Hypothesis...")
    es = ExpertSystem()

    # Resident is home, so intrusion should NOT be proven
    facts = {"MotionDetectedYard", "PerimeterArmed"} # missing NoResidentPresent
    bc = es.backward_chain("StrobeSirenActive", facts)

    assert bc["proven"] is False, "Must not prove intrusion when resident may be home"
    print("  ✓ Correctly rejected unproven hypothesis.")


if __name__ == "__main__":
    print("==================================================")
    print(" RUNNING AETHER EXPERT SYSTEM UNIT TESTS")
    print("==================================================")
    test_forward_chaining()
    test_backward_chaining_explanation()
    test_unproven_backward_query()
    print("==================================================")
    print(" ALL EXPERT SYSTEM TESTS PASSED SUCCESSFULLY! (3/3)")
    print("==================================================")
