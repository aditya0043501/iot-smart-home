"""
AETHER Classical AI Layer — Bayesian Belief Network
---------------------------------------------------
Exact Probabilistic Inference via Enumeration & Variable Elimination.
Models uncertainty for smart home occupancy and security intrusion:

  DAG Topology:
             TimeOfDay
             /       \
      ResidentHome    \
       /    |    \     \
      /     |     \     \
 Phone    Door    Intruder  Lights
  |        |        |        |
  v        v        v        v
  [Observations: WiFi, Deadbolt, PIR Motion, Luminance]

Computes exact posterior belief:
  - P(ResidentHome = True | Evidence)
  - P(Intruder = True | Evidence)
"""

from typing import Dict, List, Set, Tuple, Optional, Any
import itertools


class BayesianNode:
    """A node in the Bayesian Network with Conditional Probability Table (CPT)."""

    def __init__(
        self,
        name: str,
        parents: List[str],
        values: List[Any],
        cpt: Dict[Tuple, Dict[Any, float]],
        description: str = ""
    ):
        self.name = name
        self.parents = list(parents)
        self.values = list(values)
        self.cpt = cpt  # Key: tuple of parent values, Value: {val: prob}
        self.description = description

    def get_prob(self, value: Any, parent_assignment: Dict[str, Any]) -> float:
        """Looks up conditional probability P(name=value | parents)."""
        if not self.parents:
            parent_key = ()
        else:
            parent_key = tuple(parent_assignment[p] for p in self.parents)

        dist = self.cpt.get(parent_key, {})
        return dist.get(value, 0.0)


class SmartHomeBayesNet:
    """
    Exact Bayesian Belief Network for Smart Home Occupancy & Intrusion Estimation.
    """

    def __init__(self):
        self.nodes: Dict[str, BayesianNode] = {}
        self._build_network()

    def _build_network(self):
        # 1. TimeOfDay (Root prior)
        self.nodes["TimeOfDay"] = BayesianNode(
            name="TimeOfDay",
            parents=[],
            values=["Day", "Night"],
            cpt={
                (): {"Day": 0.65, "Night": 0.35}
            },
            description="Circadian solar phase (Day vs Night)"
        )

        # 2. ResidentHome
        # P(ResidentHome | TimeOfDay)
        self.nodes["ResidentHome"] = BayesianNode(
            name="ResidentHome",
            parents=["TimeOfDay"],
            values=[True, False],
            cpt={
                ("Day",):   {True: 0.30, False: 0.70},
                ("Night",): {True: 0.85, False: 0.15}
            },
            description="True latent occupancy state of the home"
        )

        # 3. Intruder
        # P(Intruder | TimeOfDay, ResidentHome)
        self.nodes["Intruder"] = BayesianNode(
            name="Intruder",
            parents=["TimeOfDay", "ResidentHome"],
            values=[True, False],
            cpt={
                ("Day", True):    {True: 0.001, False: 0.999},
                ("Day", False):   {True: 0.020, False: 0.980},
                ("Night", True):  {True: 0.005, False: 0.995},
                ("Night", False): {True: 0.080, False: 0.920}
            },
            description="True latent security intrusion event"
        )

        # 4. PhonePresence (WiFi / BLE probe)
        # P(PhonePresence | ResidentHome)
        self.nodes["PhonePresence"] = BayesianNode(
            name="PhonePresence",
            parents=["ResidentHome"],
            values=[True, False],
            cpt={
                (True,):  {True: 0.94, False: 0.06},
                (False,): {True: 0.03, False: 0.97}  # Rare false probe
            },
            description="Resident smartphone WiFi MAC detection"
        )

        # 5. DoorSensor
        # P(DoorSensor | ResidentHome)
        self.nodes["DoorSensor"] = BayesianNode(
            name="DoorSensor",
            parents=["ResidentHome"],
            values=["Unlocked", "Locked"],
            cpt={
                (True,):  {"Unlocked": 0.65, "Locked": 0.35},
                (False,): {"Unlocked": 0.04, "Locked": 0.96}
            },
            description="Smart lock latch state (dev-3)"
        )

        # 6. MotionDetected
        # P(MotionDetected | ResidentHome, Intruder)
        self.nodes["MotionDetected"] = BayesianNode(
            name="MotionDetected",
            parents=["ResidentHome", "Intruder"],
            values=[True, False],
            cpt={
                (True, True):   {True: 0.99, False: 0.01},
                (True, False):  {True: 0.85, False: 0.15},
                (False, True):  {True: 0.92, False: 0.08},
                (False, False): {True: 0.02, False: 0.98}  # Ambient sensor noise
            },
            description="PIR and optical motion trigger (dev-7)"
        )

        # 7. LightsOn
        # P(LightsOn | TimeOfDay, ResidentHome)
        self.nodes["LightsOn"] = BayesianNode(
            name="LightsOn",
            parents=["TimeOfDay", "ResidentHome"],
            values=[True, False],
            cpt={
                ("Day", True):    {True: 0.25, False: 0.75},
                ("Day", False):   {True: 0.01, False: 0.99},
                ("Night", True):  {True: 0.92, False: 0.08},
                ("Night", False): {True: 0.04, False: 0.96}
            },
            description="Main living room lights status (dev-1)"
        )

    def topological_order(self) -> List[str]:
        """Valid topological ordering of nodes in the DAG."""
        return ["TimeOfDay", "ResidentHome", "Intruder", "PhonePresence", "DoorSensor", "MotionDetected", "LightsOn"]

    def joint_probability(self, assignment: Dict[str, Any]) -> float:
        """P(x1, x2, ..., xn) = Product_{i} P(xi | Parents(xi))."""
        prob = 1.0
        for name in self.topological_order():
            node = self.nodes[name]
            val = assignment[name]
            p = node.get_prob(val, assignment)
            prob *= p
        return prob

    def query(
        self,
        query_var: str,
        evidence: Dict[str, Any]
    ) -> Dict[Any, float]:
        """
        Exact Inference by Enumeration:
        Computes P(query_var | evidence) = alpha * Sum_{hidden} P(query_var, hidden, evidence).
        """
        if query_var not in self.nodes:
            raise ValueError(f"Unknown query variable: {query_var}")

        node = self.nodes[query_var]
        unobserved = [v for v in self.topological_order() if v != query_var and v not in evidence]

        distribution: Dict[Any, float] = {}

        # For each possible value of the query variable
        for q_val in node.values:
            total_prob = 0.0

            # Enumerate all combinations of unobserved hidden variables
            if not unobserved:
                full_assignment = dict(evidence)
                full_assignment[query_var] = q_val
                total_prob = self.joint_probability(full_assignment)
            else:
                unobserved_domains = [self.nodes[u].values for u in unobserved]
                for combo in itertools.product(*unobserved_domains):
                    full_assignment = dict(evidence)
                    full_assignment[query_var] = q_val
                    for u_name, u_val in zip(unobserved, combo):
                        full_assignment[u_name] = u_val
                    total_prob += self.joint_probability(full_assignment)

            distribution[q_val] = total_prob

        # Normalization (alpha = 1 / sum)
        total_sum = sum(distribution.values())
        if total_sum > 0:
            for k in distribution:
                distribution[k] = round(distribution[k] / total_sum, 4)

        return distribution

    def evaluate_live_beliefs(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes simultaneous beliefs for Occupancy and Intruder given current sensor state.
        Returns percentage probabilities and top explanatory factors.
        """
        p_home = self.query("ResidentHome", evidence)
        p_intruder = self.query("Intruder", evidence)

        home_prob = p_home.get(True, 0.0)
        intruder_prob = p_intruder.get(True, 0.0)

        # Risk level classification
        if intruder_prob >= 0.50:
            risk = "CRITICAL INTRUSION RISK"
        elif intruder_prob >= 0.15:
            risk = "ELEVATED ALERT"
        elif home_prob < 0.20:
            risk = "VACANT (AWAY)"
        else:
            risk = "SECURE & OCCUPIED"

        return {
            "evidence_provided": evidence,
            "occupancy_belief": {
                "p_resident_home": home_prob,
                "p_resident_away": round(1.0 - home_prob, 4),
                "percentage_home": f"{home_prob * 100:.1f}%"
            },
            "security_belief": {
                "p_intruder_present": intruder_prob,
                "p_perimeter_safe": round(1.0 - intruder_prob, 4),
                "percentage_intruder": f"{intruder_prob * 100:.1f}%"
            },
            "overall_status": risk,
            "network_nodes": [
                {
                    "name": n.name,
                    "description": n.description,
                    "parents": n.parents,
                    "observed_value": evidence.get(n.name, "Unobserved (Marginalized)")
                }
                for n in self.nodes.values()
            ]
        }
