"""
AETHER Classical AI Layer — Fuzzy Logic Controller Unit Tests
-------------------------------------------------------------
Tests Mamdani fuzzy inference, membership functions, rule firing,
and Centroid defuzzification.
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classical.fuzzy.climate_fuzzy import ClimateFuzzyController


def test_hot_humid_climate():
    print("[TEST 1] Testing Extreme Hot & Humid Climate Modulation...")
    fuzzy = ClimateFuzzyController()
    res = fuzzy.compute(temperature=32.0, humidity=80.0, occupancy=1.0)

    # In hot and humid conditions, cooling output should be high (> 75%)
    assert res["crisp_cooling_percent"] >= 75.0, f"Expected cooling >= 75%, got {res['crisp_cooling_percent']}%"
    assert "HIGH" in res["actuator_command"]
    print(f"  ✓ High modulation verified: {res['crisp_cooling_percent']}% output.")


def test_vacant_home_energy_savings():
    print("[TEST 2] Testing Vacant Home Energy Conservation...")
    fuzzy = ClimateFuzzyController()
    res = fuzzy.compute(temperature=23.0, humidity=50.0, occupancy=0.0)

    # When vacant and comfortable, output should be in OFF range (< 15%)
    assert res["crisp_cooling_percent"] < 15.0, f"Expected cooling < 15%, got {res['crisp_cooling_percent']}%"
    assert "OFF" in res["actuator_command"]
    print(f"  ✓ Passive zero-energy state verified for vacant home ({res['crisp_cooling_percent']}%).")


def test_smooth_monotonic_increase():
    print("[TEST 3] Testing Monotonic Output Increase with Rising Temperature...")
    fuzzy = ClimateFuzzyController()

    out1 = fuzzy.compute(temperature=21.0, humidity=50.0, occupancy=1.0)["crisp_cooling_percent"]
    out2 = fuzzy.compute(temperature=26.0, humidity=50.0, occupancy=1.0)["crisp_cooling_percent"]
    out3 = fuzzy.compute(temperature=31.0, humidity=50.0, occupancy=1.0)["crisp_cooling_percent"]

    assert out1 <= out2 <= out3, f"Non-monotonic fuzzy output: {out1} -> {out2} -> {out3}"
    print(f"  ✓ Smooth monotonic response confirmed: 21°C ({out1}%) -> 26°C ({out2}%) -> 31°C ({out3}%).")


if __name__ == "__main__":
    print("==================================================")
    print(" RUNNING AETHER FUZZY CONTROLLER UNIT TESTS")
    print("==================================================")
    test_hot_humid_climate()
    test_vacant_home_energy_savings()
    test_smooth_monotonic_increase()
    print("==================================================")
    print(" ALL FUZZY CONTROLLER TESTS PASSED! (3/3)")
    print("==================================================")
