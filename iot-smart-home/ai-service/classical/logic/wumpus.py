"""
AETHER Classical AI Layer — Wumpus-World Hazard Inference Agent
--------------------------------------------------------------
Knowledge-based agent using propositional logic and model checking (TT-Entails).
Detects smart home hazards:
  - FIRE       (produces SMOKE in room and adjacent rooms)
  - GAS_LEAK   (produces STENCH in room and adjacent rooms)
  - WATER_LEAK (produces DAMPNESS in room and adjacent rooms)
  - INTRUDER   (produces FOOTSTEPS/vibrations in room and adjacent rooms)

Performs exact truth-table model checking across all $2^8 = 256$ worlds
to infer whether each room is SAFE, DANGEROUS, or UNKNOWN.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from copy import deepcopy
from dataclasses import dataclass, field
import itertools

from classical.graph.house_graph import house_graph


HAZARDS = ["FIRE", "GAS_LEAK", "WATER_LEAK", "INTRUDER"]

PERCEPT_MAP = {
    "FIRE": "SMOKE",
    "GAS_LEAK": "STENCH",
    "WATER_LEAK": "DAMP",
    "INTRUDER": "FOOTSTEPS"
}

REVERSE_PERCEPT_MAP = {v: k for k, v in PERCEPT_MAP.items()}


@dataclass
class LogicalPercept:
    room_id: str
    smoke: bool = False
    stench: bool = False
    damp: bool = False
    footsteps: bool = False

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "smoke": self.smoke,
            "stench": self.stench,
            "damp": self.damp,
            "footsteps": self.footsteps
        }


class PropositionalKB:
    """
    Propositional Logic Knowledge Base for Smart Home Hazard Inference.
    Axiom:
      Percept(r) <=> Hazard(r) OR [OR_{nbr in Adj(r)} Hazard(nbr)]
    Uses exact truth-table model checking (TT-Entails) over all 8 room hazard symbols.
    """

    def __init__(self, hazard_type: str):
        self.hazard_type = hazard_type
        self.percept_name = PERCEPT_MAP[hazard_type]
        self.facts: Dict[str, bool] = {}          # Asserted literals e.g. "FIRE_R1": False
        self.percept_facts: Dict[str, bool] = {}  # Percepts observed e.g. "SMOKE_R1": False
        self.visited_rooms: Set[str] = set()

    def tell_percept(self, room_id: str, perceived: bool):
        """Asserts percept value observed at room_id."""
        self.percept_facts[room_id] = perceived
        self.visited_rooms.add(room_id)

    def tell_hazard_absence(self, room_id: str):
        """When a room is entered and confirmed clear, it cannot contain the hazard."""
        self.facts[f"{self.hazard_type}_{room_id}"] = False

    def _get_hazard_symbols(self) -> List[str]:
        return [f"{self.hazard_type}_{rid}" for rid in house_graph.nodes.keys()]

    def is_consistent_model(self, model: Dict[str, bool]) -> bool:
        """
        Tests if a candidate truth assignment satisfies all asserted hazard facts
        and topological percept axioms:
        Percept(r) <=> Hazard(r) OR ANY(Hazard(nbr) for nbr in Adj(r))
        """
        # 1. Check known hazard facts
        for sym, val in self.facts.items():
            if model.get(sym) != val:
                return False

        # 2. Check percept axioms for all observed rooms
        for room_id, actual_percept in self.percept_facts.items():
            reach = house_graph.get_neighbors(room_id, only_passable=False) + [room_id]
            has_hazard = any(model.get(f"{self.hazard_type}_{x}", False) for x in reach)

            if actual_percept != has_hazard:
                return False

        return True

    def entails(self, query_symbol: str, query_value: bool) -> Tuple[bool, str, int, int]:
        """
        Exact TT-Entails Model Checking:
        Tests whether KB |= (query_symbol == query_value).
        Returns (is_entailed, justification_explanation, satisfying_count, valid_count).
        """
        symbols = self._get_hazard_symbols()
        n = len(symbols)

        valid_models_count = 0
        satisfying_query_count = 0

        # Exact enumeration of all 2^8 = 256 world interpretations
        for assignment in itertools.product([False, True], repeat=n):
            model = dict(zip(symbols, assignment))

            if self.is_consistent_model(model):
                valid_models_count += 1
                if model.get(query_symbol) == query_value:
                    satisfying_query_count += 1

        if valid_models_count == 0:
            return False, "Contradiction detected in sensor readings.", 0, 0

        if satisfying_query_count == valid_models_count:
            state_str = "SAFE" if not query_value else "DANGEROUS"
            return (
                True,
                f"Proven {state_str}: Holds true in all {valid_models_count} logically consistent world models.",
                satisfying_query_count,
                valid_models_count
            )

        ratio_pct = int((satisfying_query_count / valid_models_count) * 100)
        return (
            False,
            f"Indeterminate: holds in {satisfying_query_count}/{valid_models_count} ({ratio_pct}%) consistent models.",
            satisfying_query_count,
            valid_models_count
        )


class WumpusHazardAgent:
    """
    Autonomous Patrol & Hazard Identification Agent.
    Navigates through proven SAFE rooms, collects percepts,
    and updates beliefs about FIRE, GAS_LEAK, WATER_LEAK, and INTRUDER.
    """

    def __init__(self, start_room: str = "R1"):
        self.start_room = start_room
        self.current_room = start_room
        self.visited: Set[str] = {start_room}
        self.kbs: Dict[str, PropositionalKB] = {
            h: PropositionalKB(h) for h in HAZARDS
        }
        for kb in self.kbs.values():
            kb.tell_hazard_absence(start_room)

        self.room_status: Dict[str, str] = {
            rid: "UNKNOWN" for rid in house_graph.nodes.keys()
        }
        self.room_status[start_room] = "SAFE"
        self.detected_hazards: Dict[str, List[str]] = {}

    def evaluate_all_rooms(self) -> Dict[str, dict]:
        """Evaluates logical safety status for every room in the house."""
        status_report = {}

        for rid in house_graph.nodes.keys():
            is_definitely_safe = True
            confirmed_hazards = []
            explanations = []

            for h in HAZARDS:
                kb = self.kbs[h]
                h_sym = f"{h}_{rid}"

                # Test if hazard is definitely present
                entails_present, reason_pres, _, _ = kb.entails(h_sym, query_value=True)
                if entails_present:
                    confirmed_hazards.append(h)
                    explanations.append(f"{h}: {reason_pres}")
                    is_definitely_safe = False
                    continue

                # Test if hazard is definitely absent
                entails_absent, reason_abs, _, _ = kb.entails(h_sym, query_value=False)
                if not entails_absent:
                    is_definitely_safe = False
                    explanations.append(f"{h}: {reason_abs}")
                else:
                    explanations.append(f"{h}: Certified absent (Safe)")

            if confirmed_hazards:
                state = "DANGEROUS"
            elif is_definitely_safe:
                state = "SAFE"
            else:
                state = "UNKNOWN"

            self.room_status[rid] = state
            if confirmed_hazards:
                self.detected_hazards[rid] = confirmed_hazards

            status_report[rid] = {
                "room_name": house_graph.nodes[rid].name,
                "floor": house_graph.nodes[rid].floor,
                "status": state,
                "confirmed_hazards": confirmed_hazards,
                "visited": rid in self.visited,
                "is_current": rid == self.current_room,
                "reasons": explanations
            }

        return status_report

    def step(self, percept: LogicalPercept) -> dict:
        """
        Execute one step of the knowledge-based agent:
        1. Receive percepts at current location
        2. Assert percepts into Propositional KBs
        3. Clear current room of hazards
        4. Deduce new room classifications via model checking
        5. Select next safe move or finish patrol
        """
        cur = self.current_room
        self.visited.add(cur)

        # 1 & 2: Update per-hazard Knowledge Bases
        self.kbs["FIRE"].tell_percept(cur, percept.smoke)
        self.kbs["GAS_LEAK"].tell_percept(cur, percept.stench)
        self.kbs["WATER_LEAK"].tell_percept(cur, percept.damp)
        self.kbs["INTRUDER"].tell_percept(cur, percept.footsteps)

        # 3: Current room is survived
        for kb in self.kbs.values():
            kb.tell_hazard_absence(cur)

        # 4: Re-evaluate knowledge base
        report = self.evaluate_all_rooms()

        # 5: Choose next action
        neighbors = house_graph.get_neighbors(cur, only_passable=True)
        unvisited_safe_neighbors = [
            nbr for nbr in neighbors
            if nbr not in self.visited and self.room_status[nbr] == "SAFE"
        ]

        next_action = ""
        next_room = None

        if unvisited_safe_neighbors:
            next_room = unvisited_safe_neighbors[0]
            next_action = f"Move to adjacent safe room: {house_graph.nodes[next_room].name} ({next_room})"
        else:
            any_safe_unvisited = [
                rid for rid, info in report.items()
                if rid not in self.visited and info["status"] == "SAFE"
            ]
            if any_safe_unvisited:
                next_room = any_safe_unvisited[0]
                next_action = f"Backtrack to unvisited safe room: {house_graph.nodes[next_room].name} ({next_room})"
            else:
                next_action = "Patrol concluded: All accessible safe rooms verified."

        step_trace = {
            "current_room": cur,
            "current_room_name": house_graph.nodes[cur].name,
            "percepts_received": percept.to_dict(),
            "visited_rooms": list(self.visited),
            "room_evaluations": report,
            "action": next_action,
            "next_target_room": next_room,
            "confirmed_hazards": deepcopy(self.detected_hazards)
        }

        if next_room:
            self.current_room = next_room

        return step_trace


def simulate_hazard_scenario(
    hazard_location: str = "R3",
    hazard_type: str = "FIRE",
    static_sensor_rooms: Optional[List[str]] = None
) -> List[dict]:
    """
    Runs autonomous patrol simulation with a hazard injected at `hazard_location`.
    Optional `static_sensor_rooms` lets stationary sensors also feed percepts into the KB.
    Returns complete step-by-step trace list for animated UI playback.
    """
    agent = WumpusHazardAgent(start_room="R1")
    trace = []
    max_steps = 10

    # Ground truth hazard reach: room itself + adjacent rooms
    hazard_reach = house_graph.get_neighbors(hazard_location, only_passable=False) + [hazard_location]

    # Pre-load stationary sensors if provided
    if static_sensor_rooms:
        for s_room in static_sensor_rooms:
            is_active = s_room in hazard_reach
            agent.kbs[hazard_type].tell_percept(s_room, is_active)

    for step_num in range(1, max_steps + 1):
        cur = agent.current_room

        # Sensor reading at robot's current location
        p = LogicalPercept(room_id=cur)
        in_reach = cur in hazard_reach
        if in_reach:
            if hazard_type == "FIRE":
                p.smoke = True
            elif hazard_type == "GAS_LEAK":
                p.stench = True
            elif hazard_type == "WATER_LEAK":
                p.damp = True
            elif hazard_type == "INTRUDER":
                p.footsteps = True

        step_result = agent.step(p)
        step_result["step_number"] = step_num
        trace.append(step_result)

        if not step_result["next_target_room"]:
            break

    return trace


def diagnose_smart_home_sensors(active_sensor_readings: Dict[str, dict]) -> dict:
    """
    Analyzes whole-home stationary sensor readings simultaneously.
    active_sensor_readings: { "R1": {"smoke": False, "stench": False, ...}, "R2": ... }
    Returns full propositional model checking verdict for all rooms.
    """
    agent = WumpusHazardAgent(start_room="R1")

    for rid, readings in active_sensor_readings.items():
        if "smoke" in readings:
            agent.kbs["FIRE"].tell_percept(rid, bool(readings["smoke"]))
        if "stench" in readings:
            agent.kbs["GAS_LEAK"].tell_percept(rid, bool(readings["stench"]))
        if "damp" in readings:
            agent.kbs["WATER_LEAK"].tell_percept(rid, bool(readings["damp"]))
        if "footsteps" in readings:
            agent.kbs["INTRUDER"].tell_percept(rid, bool(readings["footsteps"]))

    report = agent.evaluate_all_rooms()
    return {
        "status": "success",
        "room_evaluations": report,
        "confirmed_hazards": agent.detected_hazards,
        "topology": house_graph.to_dict()
    }
