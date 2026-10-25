"""
AETHER Classical AI Layer — Bayesian Belief Network Unit Tests
--------------------------------------------------------------
Tests exact inference by enumeration for occupancy and intruder probability.
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classical.probabilistic.bayes_net import SmartHomeBayesNet


def test_normal_occupancy():
    print("[TEST 1] Testing Normal Occupancy Belief...")
    bn = SmartHomeBayesNet()

    evidence = {"TimeOfDay": "Night", "PhonePresence": True, "LightsOn": True, "MotionDetected": True}
    res = bn.evaluate_live_beliefs(evidence)

    p_home = res["occupancy_belief"]["p_resident_home"]
    p_intruder = res["security_belief"]["p_intruder_present"]

    assert p_home > 0.95, f"P(Home) should be > 95%, got {p_home}"
    assert p_intruder < 0.05, f"P(Intruder) should be < 5%, got {p_intruder}"
    assert res["overall_status"] == "SECURE & OCCUPIED"
    print(f"  ✓ Confirmed occupied home: P(Home) = {p_home*100:.1f}%, P(Intruder) = {p_intruder*100:.1f}%.")


def test_intrusion_inference():
    print("[TEST 2] Testing Security Intrusion Inference...")
    bn = SmartHomeBayesNet()

    # Suspicious pattern: Night, phone is away, motion detected, lights off
    evidence = {
        "TimeOfDay": "Night",
        "PhonePresence": False,
        "DoorSensor": "Locked",
        "MotionDetected": True,
        "LightsOn": False
    }
    res = bn.evaluate_live_beliefs(evidence)

    p_home = res["occupancy_belief"]["p_resident_home"]
    p_intruder = res["security_belief"]["p_intruder_present"]

    assert p_intruder > 0.60, f"P(Intruder) should surge > 60%, got {p_intruder}"
    assert p_home < 0.20, f"P(Home) should be low < 20%, got {p_home}"
    assert res["overall_status"] == "CRITICAL INTRUSION RISK"
    print(f"  ✓ High-confidence intrusion inferred: P(Intruder) = {p_intruder*100:.1f}%.")


def test_vacant_home():
    print("[TEST 3] Testing Vacant (Away) Home Belief...")
    bn = SmartHomeBayesNet()

    evidence = {"TimeOfDay": "Day", "PhonePresence": False, "DoorSensor": "Locked", "MotionDetected": False}
    res = bn.evaluate_live_beliefs(evidence)

    p_home = res["occupancy_belief"]["p_resident_home"]
    assert p_home < 0.05, f"P(Home) should be near 0%, got {p_home}"
    print(f"  ✓ Vacant state confirmed: P(Home) = {p_home*100:.2f}%.")


if __name__ == "__main__":
    print("==================================================")
    print(" RUNNING AETHER BAYESIAN NETWORK UNIT TESTS")
    print("==================================================")
    test_normal_occupancy()
    test_intrusion_inference()
    test_vacant_home()
    print("==================================================")
    print(" ALL BAYESIAN NETWORK TESTS PASSED! (3/3)")
    print("==================================================")
