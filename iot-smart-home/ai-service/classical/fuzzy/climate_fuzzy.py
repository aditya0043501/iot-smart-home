"""
AETHER Classical AI Layer — Mamdani Fuzzy Inference Controller
--------------------------------------------------------------
Implements:
  - Fuzzification via Triangular and Trapezoidal Membership Functions
  - Mamdani Fuzzy Rule Base with Min (T-norm) Conjunction
  - Max (S-norm) Aggregation of Output Fuzzy Sets
  - Centroid (Center of Gravity) Defuzzification

Controls Master Climate Thermostat (dev-2) and AeroFlow Fan (dev-4):
  - Inputs: Temperature (°C), Humidity (%), Occupancy Degree [0-1]
  - Output: Cooling/Fan Modulation Level [0% - 100%]
"""

from typing import Dict, List, Set, Tuple, Optional, Any


class FuzzySet:
    """Represents a fuzzy set with triangular or trapezoidal membership function."""

    def __init__(self, name: str, params: List[float], shape: str = "trapezoid"):
        self.name = name
        self.params = params  # [a, b, c, d] for trapezoid, [a, b, c] for triangle
        self.shape = shape

    def membership(self, x: float) -> float:
        """Computes membership grade mu(x) in [0.0, 1.0]."""
        if self.shape == "triangle":
            a, b, c = self.params
            if x <= a or x >= c:
                return 0.0
            elif a < x <= b:
                return (x - a) / (b - a) if b > a else 1.0
            else:
                return (c - x) / (c - b) if c > b else 1.0

        elif self.shape == "trapezoid":
            a, b, c, d = self.params
            if x < a or x > d:
                return 0.0
            elif b <= x <= c:
                return 1.0
            elif a <= x < b:
                return (x - a) / (b - a) if b > a else 1.0
            elif c < x <= d:
                return (d - x) / (d - c) if d > c else 1.0

        return 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "shape": self.shape,
            "parameters": self.params
        }


class FuzzyRule:
    """A Mamdani rule: IF antecedent_conditions THEN output_set."""

    def __init__(
        self,
        rule_id: str,
        conditions: Dict[str, str], # {"Temperature": "Hot", "Occupancy": "Occupied"}
        consequent_set: str,        # "High"
        description: str = ""
    ):
        self.rule_id = rule_id
        self.conditions = conditions
        self.consequent_set = consequent_set
        self.description = description


class ClimateFuzzyController:
    """Mamdani Fuzzy Logic Comfort Controller."""

    def __init__(self):
        # 1. Input Membership Functions
        self.temp_sets = {
            "Cold":        FuzzySet("Cold",        [16.0, 16.0, 19.0, 21.0], "trapezoid"),
            "Comfortable": FuzzySet("Comfortable", [20.0, 22.5, 25.0],       "triangle"),
            "Warm":        FuzzySet("Warm",        [23.5, 26.0, 28.5],       "triangle"),
            "Hot":         FuzzySet("Hot",         [27.0, 30.0, 36.0, 36.0], "trapezoid"),
        }

        self.humidity_sets = {
            "Dry":    FuzzySet("Dry",    [20.0, 20.0, 35.0, 45.0], "trapezoid"),
            "Normal": FuzzySet("Normal", [40.0, 52.5, 65.0],       "triangle"),
            "Humid":  FuzzySet("Humid",  [60.0, 72.0, 90.0, 90.0], "trapezoid"),
        }

        self.occupancy_sets = {
            "Vacant":   FuzzySet("Vacant",   [0.0, 0.0, 0.25, 0.45], "trapezoid"),
            "Occupied": FuzzySet("Occupied", [0.35, 0.60, 1.0, 1.0], "trapezoid"),
        }

        # 2. Output Membership Functions (Cooling/Fan Speed %)
        self.output_sets = {
            "Off":    FuzzySet("Off",    [0.0, 0.0, 10.0, 20.0],   "trapezoid"),
            "Low":    FuzzySet("Low",    [15.0, 30.0, 45.0],       "triangle"),
            "Medium": FuzzySet("Medium", [40.0, 60.0, 75.0],       "triangle"),
            "High":   FuzzySet("High",   [70.0, 85.0, 100.0, 100.0], "trapezoid"),
        }

        # 3. Rule Base
        self.rules = [
            FuzzyRule("R1", {"Temperature": "Cold"}, "Off",
                      "If temperature is cold, turn cooling off entirely."),
            FuzzyRule("R2", {"Occupancy": "Vacant", "Temperature": "Comfortable"}, "Off",
                      "If home is vacant and temp is comfortable, keep cooling off to save energy."),
            FuzzyRule("R3", {"Occupancy": "Vacant", "Temperature": "Hot"}, "Low",
                      "If home is vacant but temp is hot, run gentle ECO cooling to protect property."),
            FuzzyRule("R4", {"Temperature": "Comfortable", "Humidity": "Normal", "Occupancy": "Occupied"}, "Low",
                      "If comfortable with normal humidity and occupied, maintain low gentle air flow."),
            FuzzyRule("R5", {"Temperature": "Comfortable", "Humidity": "Humid", "Occupancy": "Occupied"}, "Medium",
                      "If comfortable but humid, increase cooling/fan to medium to dehumidify."),
            FuzzyRule("R6", {"Temperature": "Warm", "Occupancy": "Occupied"}, "Medium",
                      "If warm and occupied, engage medium cooling."),
            FuzzyRule("R7", {"Temperature": "Warm", "Humidity": "Humid", "Occupancy": "Occupied"}, "High",
                      "If warm and humid while occupied, engage high cooling."),
            FuzzyRule("R8", {"Temperature": "Hot", "Occupancy": "Occupied"}, "High",
                      "If hot and occupied, run AC compressor and fan at maximum high output."),
            FuzzyRule("R9", {"Temperature": "Hot", "Humidity": "Humid"}, "High",
                      "If both hot and humid, run at maximum cooling capacity."),
        ]

    def compute(
        self,
        temperature: float,
        humidity: float,
        occupancy: float
    ) -> Dict[str, Any]:
        """
        Executes full Mamdani Fuzzy Inference Pipeline:
          1. Fuzzification
          2. Rule firing strength evaluation
          3. Output set aggregation
          4. Centroid defuzzification
        """
        # 1. Fuzzify crisp inputs
        t_mems = {k: s.membership(temperature) for k, s in self.temp_sets.items()}
        h_mems = {k: s.membership(humidity) for k, s in self.humidity_sets.items()}
        o_mems = {k: s.membership(occupancy) for k, s in self.occupancy_sets.items()}

        all_input_mems = {
            "Temperature": t_mems,
            "Humidity": h_mems,
            "Occupancy": o_mems
        }

        # 2. Evaluate Rule Firing Strengths (min t-norm)
        rule_activations: List[dict] = []
        consequent_weights: Dict[str, float] = {k: 0.0 for k in self.output_sets.keys()}

        for rule in self.rules:
            # Strength = min over all condition memberships
            strengths = []
            for var_name, set_name in rule.conditions.items():
                strengths.append(all_input_mems[var_name][set_name])

            rule_strength = min(strengths) if strengths else 0.0

            # Aggregate via max (S-norm)
            consequent_weights[rule.consequent_set] = max(
                consequent_weights[rule.consequent_set],
                rule_strength
            )

            if rule_strength > 0.001:
                rule_activations.append({
                    "rule_id": rule.rule_id,
                    "firing_strength": round(rule_strength, 4),
                    "consequent": rule.consequent_set,
                    "description": rule.description
                })

        # 3. Centroid Defuzzification (Numerical Integration over [0, 100])
        # Sample points y from 0 to 100 in steps of 1.0
        numerator = 0.0
        denominator = 0.0
        aggregated_curve = []

        for y in range(0, 101):
            y_float = float(y)
            # mu_agg(y) = max_k min(weight_k, set_k.membership(y))
            mu_y = max(
                min(consequent_weights[set_name], out_set.membership(y_float))
                for set_name, out_set in self.output_sets.items()
            )
            numerator += y_float * mu_y
            denominator += mu_y
            if y % 5 == 0:  # Sample for UI curve
                aggregated_curve.append({"output_percent": y, "membership": round(mu_y, 4)})

        crisp_output = round(numerator / denominator, 2) if denominator > 0.0 else 0.0

        # Map to device actuation levels
        if crisp_output < 15.0:
            actuator_cmd = "OFF (Passive)"
        elif crisp_output < 45.0:
            actuator_cmd = "LOW (ECO Cooling)"
        elif crisp_output < 75.0:
            actuator_cmd = "MEDIUM (Comfort Cooling)"
        else:
            actuator_cmd = "HIGH (Maximum AC & Turbo Fan)"

        return {
            "inputs": {
                "temperature_celsius": temperature,
                "humidity_percent": humidity,
                "occupancy_index": occupancy
            },
            "crisp_cooling_percent": crisp_output,
            "actuator_command": actuator_cmd,
            "fuzzified_inputs": {
                var: {k: round(v, 3) for k, v in dist.items()}
                for var, dist in all_input_mems.items()
            },
            "active_rules_fired": rule_activations,
            "defuzzification": {
                "method": "Centroid (Center of Gravity)",
                "consequent_firing_strengths": {k: round(v, 4) for k, v in consequent_weights.items()},
                "aggregated_curve": aggregated_curve
            }
        }
