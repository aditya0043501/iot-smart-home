"""
AETHER AI Service — Classical AI REST API Endpoints
---------------------------------------------------
Exposes clean endpoints for:
  - House Graph Topology
  - Wumpus World Hazard Inference (Patrol Simulation & Stationary Sensor Diagnosis)
  - Subsequent classical modules (Search, Planning, CSP, Bayes, MDP, Fuzzy, Optimization)
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from classical.graph.house_graph import house_graph
from classical.logic.wumpus import (
    simulate_hazard_scenario,
    diagnose_smart_home_sensors,
    HAZARDS
)
from classical.planning.strips import (
    STRIPSPlanner,
    PRESET_GOALS,
    get_default_initial_state
)
from classical.search.routing import SearchComparisonEngine
from classical.csp.scheduler import ApplianceCSPSolver, get_default_appliances
from classical.logic.expert_system import ExpertSystem, get_default_smart_home_rules
from classical.probabilistic.bayes_net import SmartHomeBayesNet
from classical.probabilistic.mdp_thermostat import ThermostatMDP
from classical.fuzzy.climate_fuzzy import ClimateFuzzyController
from classical.optimization.energy_opt import (
    OptimizerEngine,
    HOURLY_TARIFF,
    APPLIANCES_TO_OPTIMIZE
)

planner = STRIPSPlanner()
search_engine = SearchComparisonEngine()
csp_solver = ApplianceCSPSolver()
expert_system = ExpertSystem()
bayes_net = SmartHomeBayesNet()
thermostat_mdp = ThermostatMDP()
fuzzy_controller = ClimateFuzzyController()
optimizer_engine = OptimizerEngine()

classical_router = APIRouter(prefix="/api/classical", tags=["classical-ai"])


# ── House Graph Topology ─────────────────────────────────────

@classical_router.get("/graph")
def get_house_graph():
    """Returns the complete smart villa room graph (nodes, edges, devices, exits)."""
    return house_graph.to_dict()


# ── Wumpus World Hazard Inference ────────────────────────────

class WumpusSimRequest(BaseModel):
    hazard_location: str = Field("R3", description="Room ID containing the hazard, e.g. R3")
    hazard_type: str = Field("FIRE", description="FIRE, GAS_LEAK, WATER_LEAK, or INTRUDER")
    static_sensor_rooms: Optional[List[str]] = Field(None, description="Optional list of static sensors online")


@classical_router.post("/wumpus/simulate")
def run_wumpus_simulation(req: WumpusSimRequest):
    """
    Simulates autonomous patrol agent navigating using propositional model checking.
    Returns complete step-by-step trace with logic justifications for animated playback.
    """
    if req.hazard_location not in house_graph.nodes:
        raise HTTPException(status_code=400, detail=f"Invalid room ID: {req.hazard_location}")
    if req.hazard_type not in HAZARDS:
        raise HTTPException(status_code=400, detail=f"Invalid hazard type: {req.hazard_type}. Allowed: {HAZARDS}")

    trace = simulate_hazard_scenario(
        hazard_location=req.hazard_location,
        hazard_type=req.hazard_type,
        static_sensor_rooms=req.static_sensor_rooms
    )

    return {
        "status": "success",
        "hazard_location": req.hazard_location,
        "hazard_type": req.hazard_type,
        "total_steps": len(trace),
        "trace": trace,
        "final_confirmed_hazards": trace[-1]["confirmed_hazards"] if trace else {}
    }


class WumpusDiagnoseRequest(BaseModel):
    sensor_readings: Dict[str, Dict[str, bool]] = Field(
        ...,
        description="Map of room_id -> percept dict, e.g. {'R1': {'smoke': false}, 'R2': {'smoke': true}}"
    )


@classical_router.post("/wumpus/diagnose")
def run_wumpus_diagnose(req: WumpusDiagnoseRequest):
    """
    Performs full truth-table model checking across all whole-home sensor readings.
    """
    result = diagnose_smart_home_sensors(req.sensor_readings)
    return result


# ── STRIPS Automated Planner ─────────────────────────────────

@classical_router.get("/planning/presets")
def get_planning_presets():
    """Returns preset smart home goals (movie night, leave home, etc.)."""
    return {
        "presets": {
            k: {
                "title": v["title"],
                "description": v["description"],
                "goal_predicates": sorted(list(v["goal_predicates"]))
            }
            for k, v in PRESET_GOALS.items()
        },
        "default_state": sorted(list(get_default_initial_state()))
    }


class PlanSolveRequest(BaseModel):
    goal_key: Optional[str] = Field("movie_night", description="Key from PRESET_GOALS or custom")
    custom_goals: Optional[List[str]] = Field(None, description="Custom goal predicates list")
    initial_state: Optional[List[str]] = Field(None, description="Optional custom initial state")


@classical_router.post("/planning/solve")
def solve_strips_plan(req: PlanSolveRequest):
    """Computes optimal action plan to achieve target smart home goal."""
    if req.custom_goals:
        goals = set(req.custom_goals)
    elif req.goal_key in PRESET_GOALS:
        goals = PRESET_GOALS[req.goal_key]["goal_predicates"]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown goal key: {req.goal_key}")

    s0 = set(req.initial_state) if req.initial_state else get_default_initial_state()
    result = planner.solve(s0, goals)
    return result


class PlanReplanRequest(BaseModel):
    goal_key: str = Field("movie_night", description="Goal key to achieve")
    failed_device_id: str = Field("dev-1", description="Device that encountered hardware failure")


@classical_router.post("/planning/replan")
def replan_on_device_failure(req: PlanReplanRequest):
    """Triggers dynamic replanning when a smart home device fails or goes offline."""
    if req.goal_key not in PRESET_GOALS:
        raise HTTPException(status_code=400, detail=f"Unknown goal key: {req.goal_key}")

    goals = PRESET_GOALS[req.goal_key]["goal_predicates"]
    s0 = get_default_initial_state()
    replan_result = planner.replan_on_failure(s0, goals, failed_device_id=req.failed_device_id)
    return replan_result


# ── Search & Evacuation Routing ──────────────────────────────

class SearchCompareRequest(BaseModel):
    start_room: str = Field("R7", description="Starting room ID, e.g. R7 (Master Bedroom)")
    goals: Optional[List[str]] = Field(None, description="Optional target exit room IDs")
    blocked_rooms: Optional[List[str]] = Field(None, description="Rooms blocked by fire, debris, or hazards")
    heuristic: str = Field("euclidean", description="'euclidean' or 'manhattan'")


@classical_router.post("/search/compare")
def compare_search_algorithms(req: SearchCompareRequest):
    """
    Runs BFS, DFS, UCS, Greedy, and A* side-by-side on the identical routing task.
    Returns comparison matrix, optimality indicators, and step traces.
    """
    if req.start_room not in house_graph.nodes:
        raise HTTPException(status_code=400, detail=f"Invalid start room: {req.start_room}")

    result = search_engine.compare_all(
        start=req.start_room,
        goals=req.goals,
        blocked_rooms=req.blocked_rooms,
        heuristic_type=req.heuristic
    )
    return result


class VacuumCoverageRequest(BaseModel):
    start_room: str = Field("R1", description="Dock room location, e.g. R1")


@classical_router.post("/search/vacuum")
def compute_vacuum_coverage_plan(req: VacuumCoverageRequest):
    """Computes complete-coverage tour across all villa rooms for robotic vacuum cleaner."""
    if req.start_room not in house_graph.nodes:
        raise HTTPException(status_code=400, detail=f"Invalid dock room: {req.start_room}")

    return search_engine.compute_vacuum_coverage(start=req.start_room)


# ── Constraint Satisfaction Problem (CSP) Appliance Scheduler ─

@classical_router.get("/csp/appliances")
def get_csp_appliances():
    """Returns list of appliances, default domains, deadlines, and power draws."""
    apps = get_default_appliances()
    return {
        "appliances": [a.to_dict() for a in apps.values()],
        "default_power_cap_watts": 3800.0,
        "default_horizon_slots": 12
    }


class CSPSolveRequest(BaseModel):
    power_cap_watts: float = Field(3500.0, description="Peak allowable home grid power in Watts")
    horizon_slots: int = Field(12, description="Scheduling horizon duration in hours")
    use_ac3: bool = Field(True, description="Enable AC-3 arc consistency preprocessing")


@classical_router.post("/csp/solve")
def solve_appliance_csp(req: CSPSolveRequest):
    """Solves appliance schedule using AC-3 arc consistency, MRV, and BT-FC."""
    solver = ApplianceCSPSolver(
        power_cap_watts=req.power_cap_watts,
        total_horizon_slots=req.horizon_slots
    )
    result = solver.solve(use_ac3=req.use_ac3)
    return result


# ── Expert System (Forward & Backward Chaining) ──────────────

@classical_router.get("/expert/rules")
def get_expert_rules():
    """Returns all Horn-clause production rules in the expert knowledge base."""
    rules = get_default_smart_home_rules()
    return {"rules": [r.to_dict() for r in rules]}


class ForwardChainRequest(BaseModel):
    facts: List[str] = Field(
        ["WindowOpen", "ACOn"],
        description="List of observed ground facts, e.g. ['WindowOpen', 'ACOn']"
    )


@classical_router.post("/expert/forward")
def run_forward_chaining(req: ForwardChainRequest):
    """Data-driven forward chaining: deduces all cascading alerts and automated actions."""
    return expert_system.forward_chain(set(req.facts))


class BackwardChainRequest(BaseModel):
    goal: str = Field("StrobeSirenActive", description="Conclusion hypothesis to explain, e.g. 'StrobeSirenActive'")
    known_facts: List[str] = Field(
        ["MotionDetectedYard", "PerimeterArmed", "NoResidentPresent"],
        description="Current ground sensor facts asserted in memory"
    )


@classical_router.post("/expert/backward")
def run_backward_chaining(req: BackwardChainRequest):
    """Goal-driven backward chaining: answers 'Why is this active?' with an AND/OR proof tree."""
    return expert_system.backward_chain(req.goal, set(req.known_facts))


# ── Bayesian Belief Network (Occupancy & Security) ───────────

@classical_router.get("/bayes/structure")
def get_bayes_network_structure():
    """Returns Bayesian network nodes, conditional probability dependencies, and parent links."""
    return {
        "nodes": [
            {
                "name": n.name,
                "description": n.description,
                "parents": n.parents,
                "possible_values": n.values
            }
            for n in bayes_net.nodes.values()
        ]
    }


class BayesQueryRequest(BaseModel):
    evidence: Dict[str, Any] = Field(
        {"TimeOfDay": "Night", "PhonePresence": True, "MotionDetected": True},
        description="Sensor evidence dictionary, e.g. {'TimeOfDay': 'Night', 'PhonePresence': false, 'MotionDetected': true}"
    )


@classical_router.post("/bayes/query")
def query_bayes_beliefs(req: BayesQueryRequest):
    """
    Performs exact inference by enumeration to compute live beliefs
    for P(ResidentHome) and P(Intruder) given evidence.
    """
    return bayes_net.evaluate_live_beliefs(req.evidence)


# ── Markov Decision Process (MDP) Value Iteration ────────────

class MDPSolveRequest(BaseModel):
    gamma: float = Field(0.92, description="Discount factor (0.5 to 0.99)")
    epsilon: float = Field(0.001, description="Convergence delta threshold")
    outdoor_bias: str = Field("Hot", description="Warm climate bias ('Hot' or 'Cold')")


@classical_router.post("/mdp/solve")
def solve_thermostat_mdp(req: MDPSolveRequest):
    """
    Runs Bellman Value Iteration to compute optimal thermostat control policy
    balancing occupant comfort vs energy cost.
    """
    mdp = ThermostatMDP(
        gamma=req.gamma,
        epsilon=req.epsilon,
        ambient_outdoor_bias=req.outdoor_bias
    )
    return mdp.value_iteration()


# ── Mamdani Fuzzy Logic Comfort Controller ───────────────────

class FuzzyComputeRequest(BaseModel):
    temperature: float = Field(26.5, description="Ambient temperature in °C (16 to 36)")
    humidity: float = Field(65.0, description="Relative humidity in % (20 to 90)")
    occupancy: float = Field(0.8, description="Occupancy index (0.0=vacant to 1.0=fully occupied)")


@classical_router.post("/fuzzy/compute")
def compute_fuzzy_climate(req: FuzzyComputeRequest):
    """
    Evaluates Mamdani fuzzy inference with Centroid defuzzification
    for smooth AC compressor & fan speed modulation.
    """
    return fuzzy_controller.compute(
        temperature=req.temperature,
        humidity=req.humidity,
        occupancy=req.occupancy
    )


# ── Local Search & Evolutionary Optimization ─────────────────

@classical_router.get("/optimization/tariffs")
def get_optimization_tariffs():
    """Returns 24h dynamic electricity tariff schedule and appliances to shift."""
    return {
        "hourly_tariffs_inr": HOURLY_TARIFF,
        "appliances": APPLIANCES_TO_OPTIMIZE,
        "peak_hours": ["10:00 - 14:00", "18:00 - 22:00"],
        "off_peak_hours": ["00:00 - 06:00"]
    }


class OptimizationCompareRequest(BaseModel):
    seed_schedule: Optional[List[int]] = Field(
        None,
        description="Optional 5-integer list of unoptimized start hours, e.g. [8, 12, 11, 19, 18]"
    )


@classical_router.post("/optimization/compare")
def compare_optimization_algorithms(req: OptimizationCompareRequest):
    """
    Runs Hill Climbing, Simulated Annealing, and Genetic Algorithm on the same
    energy-cost load-shifting problem. Returns side-by-side convergence curves.
    """
    return optimizer_engine.compare_all(seed_schedule=req.seed_schedule)
