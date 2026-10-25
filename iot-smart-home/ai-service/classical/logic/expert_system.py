"""
AETHER Classical AI Layer — Rule-Based Expert System
---------------------------------------------------
Implements:
  - Forward Chaining (Data-driven sensor reactive inference)
  - Backward Chaining (Goal-driven diagnostic root-cause explanation)
  - AND/OR Proof Tree generation for UI explainability

Answers questions like:
  - "Given new sensor readings, what automated actions and alerts fire?"
  - "Why is the alarm sounding?" (Traces back to primary sensor facts)
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from copy import deepcopy


class Rule:
    """A Horn-clause production rule: IF all(antecedents) THEN consequent."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        antecedents: List[str],
        consequent: str,
        description: str = "",
        severity: str = "INFO"  # INFO, WARNING, CRITICAL
    ):
        self.rule_id = rule_id
        self.name = name
        self.antecedents = list(antecedents)
        self.consequent = consequent
        self.description = description
        self.severity = severity

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "if_conditions": self.antecedents,
            "then_consequent": self.consequent,
            "description": self.description,
            "severity": self.severity
        }


def get_default_smart_home_rules() -> List[Rule]:
    """Canonical smart home expert rule base."""
    return [
        Rule(
            rule_id="R-ENERGY-01",
            name="Energy Waste Alert",
            antecedents=["WindowOpen", "ACOn"],
            consequent="EnergyWasteAlert",
            description="Leaving a window open while AC is active causes thermal loss and energy waste.",
            severity="WARNING"
        ),
        Rule(
            rule_id="R-ENERGY-02",
            name="Eco Chime Notification",
            antecedents=["EnergyWasteAlert"],
            consequent="PlayEcoAudioChime",
            description="Sound gentle chime through living room speaker to notify resident.",
            severity="INFO"
        ),
        Rule(
            rule_id="R-SEC-01",
            name="Unauthorized Intrusion Detection",
            antecedents=["MotionDetectedYard", "PerimeterArmed", "NoResidentPresent"],
            consequent="IntrusionAlarmTriggered",
            description="Perimeter motion detected while property is armed and residents are away.",
            severity="CRITICAL"
        ),
        Rule(
            rule_id="R-SEC-02",
            name="Perimeter Strobe Siren Activation",
            antecedents=["IntrusionAlarmTriggered"],
            consequent="StrobeSirenActive",
            description="Engage outdoor flashing strobe and 105dB security siren.",
            severity="CRITICAL"
        ),
        Rule(
            rule_id="R-SEC-03",
            name="Emergency Security Dispatch Alert",
            antecedents=["IntrusionAlarmTriggered"],
            consequent="SendSecurityDispatchAlert",
            description="Transmit automated high-priority alert to resident mobile app and central guard station.",
            severity="CRITICAL"
        ),
        Rule(
            rule_id="R-SEC-04",
            name="Nighttime Unlocked Door Hazard",
            antecedents=["NightTime", "FrontDoorUnlocked"],
            consequent="SecurityVulnerabilityAlert",
            description="Front entrance left unlocked after dark poses security risk.",
            severity="WARNING"
        ),
        Rule(
            rule_id="R-SEC-05",
            name="Auto-Lock Enforcement",
            antecedents=["SecurityVulnerabilityAlert"],
            consequent="TriggerMotorizedAutoLock",
            description="Automatically trigger smart deadbolt motor to secure entrance.",
            severity="INFO"
        ),
        Rule(
            rule_id="R-CLIM-01",
            name="Thermal Heat Stress Advisory",
            antecedents=["AmbientTempAbove30", "ACModeEco"],
            consequent="ThermalDiscomfortWarning",
            description="Room temperature exceeds comfort threshold under ECO mode.",
            severity="WARNING"
        ),
        Rule(
            rule_id="R-SAFE-01",
            name="Unattended Kitchen Cooking Warning",
            antecedents=["OvenHeatingActive", "NoKitchenMotionFor30m"],
            consequent="KitchenFireHazardWarning",
            description="High-wattage oven active with no motion detected in kitchen for 30 minutes.",
            severity="CRITICAL"
        ),
        Rule(
            rule_id="R-GRID-01",
            name="Peak Tariff Solar Peak Shaving",
            antecedents=["PeakGridTariffHours", "SolarBatteryAbove60"],
            consequent="SwitchToBatteryPower",
            description="Switch high-draw appliances to solar battery storage to avoid expensive peak grid rates.",
            severity="INFO"
        ),
    ]


class ExpertSystem:
    """Propositional Forward and Backward Chaining Inference Engine."""

    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules = rules or get_default_smart_home_rules()

    # ── 1. Forward Chaining ────────────────────────────────────
    def forward_chain(self, initial_facts: Set[str]) -> Dict[str, Any]:
        """
        Data-driven reasoning:
        Derives all logical consequences from asserted ground sensor facts.
        """
        known_facts = set(initial_facts)
        firing_history = []
        iteration = 0
        rules_fired_this_pass = True

        while rules_fired_this_pass:
            iteration += 1
            rules_fired_this_pass = False

            for rule in self.rules:
                # Rule fires iff all antecedents are known and consequent is not yet known
                if rule.consequent not in known_facts:
                    if all(ante in known_facts for ante in rule.antecedents):
                        known_facts.add(rule.consequent)
                        rules_fired_this_pass = True
                        firing_history.append({
                            "iteration": iteration,
                            "rule_id": rule.rule_id,
                            "rule_name": rule.name,
                            "triggered_by": list(rule.antecedents),
                            "derived_fact": rule.consequent,
                            "severity": rule.severity,
                            "description": rule.description
                        })

        new_inferred = known_facts - set(initial_facts)

        return {
            "initial_facts": sorted(list(initial_facts)),
            "new_inferred_facts": sorted(list(new_inferred)),
            "total_facts": sorted(list(known_facts)),
            "firing_trace": firing_history,
            "total_rules_fired": len(firing_history)
        }

    # ── 2. Backward Chaining ───────────────────────────────────
    def backward_chain(self, query_goal: str, known_facts: Set[str]) -> Dict[str, Any]:
        """
        Goal-driven reasoning:
        Answers 'Why is [query_goal] active?' by generating an AND/OR proof tree
        tracing conclusions back to primary sensor facts.
        """
        proof_path = []
        visited_subgoals: Set[str] = set()

        def prove(goal: str, depth: int = 0) -> Tuple[bool, dict]:
            indent = "  " * depth

            # Base Case 1: Fact already known from empirical sensor data
            if goal in known_facts:
                node = {
                    "goal": goal,
                    "proven": True,
                    "type": "FACT",
                    "explanation": f"Observed sensor fact: '{goal}' is TRUE."
                }
                return True, node

            # Cycle detection
            if goal in visited_subgoals:
                return False, {"goal": goal, "proven": False, "type": "CYCLE"}

            visited_subgoals.add(goal)

            # Find all rules that could conclude this goal
            candidate_rules = [r for r in self.rules if r.consequent == goal]

            if not candidate_rules:
                return False, {
                    "goal": goal,
                    "proven": False,
                    "type": "UNKNOWN",
                    "explanation": f"No rule or sensor fact establishes '{goal}'."
                }

            # Try candidate rules (OR branch)
            for rule in candidate_rules:
                subgoal_nodes = []
                all_subgoals_proven = True

                # All antecedents of this rule must hold (AND branch)
                for ante in rule.antecedents:
                    sub_ok, sub_node = prove(ante, depth + 1)
                    subgoal_nodes.append(sub_node)
                    if not sub_ok:
                        all_subgoals_proven = False
                        break

                if all_subgoals_proven:
                    proof_node = {
                        "goal": goal,
                        "proven": True,
                        "type": "RULE",
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "description": rule.description,
                        "severity": rule.severity,
                        "children": subgoal_nodes,
                        "explanation": f"Proven via rule [{rule.rule_id}] '{rule.name}': All antecedents verified."
                    }
                    return True, proof_node

            return False, {
                "goal": goal,
                "proven": False,
                "type": "UNPROVEN",
                "explanation": f"Could not satisfy antecedents for goal '{goal}'."
            }

        is_proven, proof_tree = prove(query_goal)

        # Build human-readable diagnostic summary
        def flatten_reasons(node: dict) -> List[str]:
            reasons = []
            if node.get("type") == "FACT":
                reasons.append(f"Sensor confirms: {node['goal']}")
            elif node.get("type") == "RULE":
                reasons.append(f"Rule [{node['rule_id']}] {node['rule_name']}")
                for child in node.get("children", []):
                    reasons.extend(flatten_reasons(child))
            return reasons

        summary_reasons = flatten_reasons(proof_tree) if is_proven else [f"Goal '{query_goal}' could not be established."]

        return {
            "query_goal": query_goal,
            "proven": is_proven,
            "root_explanation": summary_reasons,
            "proof_tree": proof_tree
        }
