"""
AETHER Classical AI Layer — STRIPS Automated Planner
----------------------------------------------------
Classical STRIPS forward state-space progression planner.
Solves goal-based smart home automations:
  - "movie_night"
  - "leave_home"
  - "sleep_mode"
  - "morning_routine"

Supports:
  - Propositional states, preconditions, add-lists, and delete-lists
  - A* forward search with goal-counting heuristic
  - Dynamic replanning when a device fails or goes offline
  - Full execution trace for UI step-by-step visualization
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from copy import deepcopy
import heapq


class Action:
    """A STRIPS Operator with preconditions, add effects, and delete effects."""

    def __init__(
        self,
        name: str,
        preconditions: Set[str],
        add_effects: Set[str],
        del_effects: Set[str],
        cost: float = 1.0,
        device_id: Optional[str] = None,
        description: str = ""
    ):
        self.name = name
        self.preconditions = set(preconditions)
        self.add_effects = set(add_effects)
        self.del_effects = set(del_effects)
        self.cost = cost
        self.device_id = device_id
        self.description = description

    def is_applicable(self, state: Set[str]) -> bool:
        """Action can execute iff all preconditions are present in the state."""
        return self.preconditions.issubset(state)

    def apply(self, state: Set[str]) -> Set[str]:
        """Returns successor state: (state - del_effects) U add_effects."""
        return (state - self.del_effects) | self.add_effects

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "device_id": self.device_id,
            "cost": self.cost,
            "preconditions": sorted(list(self.preconditions)),
            "add_effects": sorted(list(self.add_effects)),
            "del_effects": sorted(list(self.del_effects))
        }


def get_smart_home_domain() -> List[Action]:
    """Canonical STRIPS operators available in the AETHER smart villa."""
    return [
        # --- Lighting Actions ---
        Action(
            name="TurnOnLivingLights",
            preconditions={"PowerAvailable", "DeviceOnline_dev1"},
            add_effects={"LivingLightsOn"},
            del_effects={"LivingLightsOff", "LivingLightsDimmed"},
            device_id="dev-1",
            description="Turn on living room main lights (100% brightness)."
        ),
        Action(
            name="DimLivingLights",
            preconditions={"PowerAvailable", "DeviceOnline_dev1"},
            add_effects={"LivingLightsDimmed"},
            del_effects={"LivingLightsOn", "LivingLightsOff"},
            device_id="dev-1",
            description="Dim living room main lights to 20% for cinematic atmosphere."
        ),
        Action(
            name="TurnOffLivingLights",
            preconditions={"PowerAvailable", "DeviceOnline_dev1"},
            add_effects={"LivingLightsOff"},
            del_effects={"LivingLightsOn", "LivingLightsDimmed"},
            device_id="dev-1",
            description="Turn off living room main lights completely."
        ),
        Action(
            name="TurnOnBedroomLamp",
            preconditions={"PowerAvailable", "DeviceOnline_dev5"},
            add_effects={"BedroomLampOn"},
            del_effects={"BedroomLampOff"},
            device_id="dev-5",
            description="Turn on bedroom bedside reading lamp."
        ),
        Action(
            name="TurnOffBedroomLamp",
            preconditions={"PowerAvailable", "DeviceOnline_dev5"},
            add_effects={"BedroomLampOff"},
            del_effects={"BedroomLampOn"},
            device_id="dev-5",
            description="Turn off bedroom bedside reading lamp."
        ),
        # Fallback lighting if dev-1 fails
        Action(
            name="TurnOnAmbientAccentStrips",
            preconditions={"PowerAvailable", "DeviceOnline_strips"},
            add_effects={"LivingLightsDimmed"},
            del_effects={"LivingLightsOff"},
            device_id="strips",
            description="Fallback: Turn on living room LED accent strips when main lights offline."
        ),

        # --- Climate / Thermostat / Fan ---
        Action(
            name="SetClimateCool22",
            preconditions={"PowerAvailable", "DeviceOnline_dev2"},
            add_effects={"ClimateCool22"},
            del_effects={"ClimateEco", "ClimateNight24"},
            device_id="dev-2",
            description="Set master thermostat to Comfort Cooling (22°C)."
        ),
        Action(
            name="SetClimateNight24",
            preconditions={"PowerAvailable", "DeviceOnline_dev2"},
            add_effects={"ClimateNight24"},
            del_effects={"ClimateCool22", "ClimateEco"},
            device_id="dev-2",
            description="Set master thermostat to Night Sleep Mode (24°C)."
        ),
        Action(
            name="SetClimateEco",
            preconditions={"PowerAvailable", "DeviceOnline_dev2"},
            add_effects={"ClimateEco"},
            del_effects={"ClimateCool22", "ClimateNight24"},
            device_id="dev-2",
            description="Set master thermostat to Energy-Saving Eco Mode (28°C)."
        ),
        Action(
            name="SetFanLow",
            preconditions={"PowerAvailable", "DeviceOnline_dev4"},
            add_effects={"FanSpeedLow"},
            del_effects={"FanSpeedMedium", "FanSpeedOff"},
            device_id="dev-4",
            description="Set AeroFlow ceiling fan to gentle Low speed."
        ),
        Action(
            name="TurnOffFan",
            preconditions={"PowerAvailable", "DeviceOnline_dev4"},
            add_effects={"FanSpeedOff"},
            del_effects={"FanSpeedLow", "FanSpeedMedium"},
            device_id="dev-4",
            description="Turn off bedroom ceiling fan."
        ),

        # --- Security & Access ---
        Action(
            name="LockFrontEntrance",
            preconditions={"DeviceOnline_dev3"},
            add_effects={"DoorsLocked"},
            del_effects={"DoorsUnlocked"},
            device_id="dev-3",
            description="Engage motorized deadbolt on front entrance."
        ),
        Action(
            name="UnlockFrontEntrance",
            preconditions={"DeviceOnline_dev3"},
            add_effects={"DoorsUnlocked"},
            del_effects={"DoorsLocked"},
            device_id="dev-3",
            description="Unlock front entrance smart deadbolt."
        ),
        Action(
            name="ArmSecurityCamera",
            preconditions={"PowerAvailable", "DeviceOnline_dev7"},
            add_effects={"SecurityArmed", "CameraRecording"},
            del_effects={"SecurityDisarmed"},
            device_id="dev-7",
            description="Arm perimeter HD camera and enable AI motion alerts."
        ),
        Action(
            name="DisarmSecurityCamera",
            preconditions={"PowerAvailable", "DeviceOnline_dev7"},
            add_effects={"SecurityDisarmed"},
            del_effects={"SecurityArmed", "CameraRecording"},
            device_id="dev-7",
            description="Disarm security cameras for resident arrival."
        ),

        # --- Entertainment & Comfort ---
        Action(
            name="CloseMotorizedCurtains",
            preconditions={"PowerAvailable", "DeviceOnline_curtains"},
            add_effects={"CurtainsClosed"},
            del_effects={"CurtainsOpen"},
            device_id="curtains",
            description="Close motorized blackout curtains in living room."
        ),
        Action(
            name="OpenMotorizedCurtains",
            preconditions={"PowerAvailable", "DeviceOnline_curtains"},
            add_effects={"CurtainsOpen"},
            del_effects={"CurtainsClosed"},
            device_id="curtains",
            description="Open motorized living room curtains to let in morning daylight."
        ),
        Action(
            name="TurnOnCinemaDisplay",
            preconditions={"PowerAvailable", "DeviceOnline_tv", "CurtainsClosed"},
            add_effects={"TVCinemaOn"},
            del_effects={"TVCinemaOff"},
            device_id="tv",
            description="Power on 4K Smart TV and select Home Cinema profile (requires curtains closed)."
        ),
        Action(
            name="TurnOffCinemaDisplay",
            preconditions={"PowerAvailable", "DeviceOnline_tv"},
            add_effects={"TVCinemaOff"},
            del_effects={"TVCinemaOn"},
            device_id="tv",
            description="Power off 4K Smart TV display."
        ),

        # --- Kitchen Appliances ---
        Action(
            name="BrewMorningEspresso",
            preconditions={"PowerAvailable", "DeviceOnline_dev6", "WaterReservoirFull"},
            add_effects={"CoffeeBrewed"},
            del_effects={"CoffeeMakerIdle"},
            device_id="dev-6",
            description="Brew hot morning espresso via Smart Coffee Maker."
        ),
        Action(
            name="PowerOffKitchenAppliances",
            preconditions={"PowerAvailable"},
            add_effects={"AppliancesStandby"},
            del_effects={"OvenActive", "CoffeeBrewing"},
            device_id="kitchen",
            description="Ensure oven, coffee maker, and cooktop are in safe standby."
        )
    ]


PRESET_GOALS: Dict[str, Dict[str, Any]] = {
    "movie_night": {
        "title": "Movie Night Atmosphere",
        "description": "Prepare living room for film screening: blackout shades, dimmed lighting, TV online, cool temp.",
        "goal_predicates": {"CurtainsClosed", "LivingLightsDimmed", "TVCinemaOn", "ClimateCool22", "FanSpeedOff"}
    },
    "leave_home": {
        "title": "Secure Departure (Away Mode)",
        "description": "Lock all access doors, shut off all lights, switch AC to ECO, arm security camera perimeter.",
        "goal_predicates": {"DoorsLocked", "LivingLightsOff", "BedroomLampOff", "ClimateEco", "SecurityArmed", "TVCinemaOff", "AppliancesStandby"}
    },
    "sleep_mode": {
        "title": "Night Sleep Mode",
        "description": "Lock doors, arm security, switch lights off, activate bedside lamp off, fan low, set temp 24°C.",
        "goal_predicates": {"DoorsLocked", "LivingLightsOff", "BedroomLampOff", "FanSpeedLow", "ClimateNight24", "SecurityArmed"}
    },
    "morning_routine": {
        "title": "Morning Wakeup & Comfort",
        "description": "Open window curtains, brew fresh espresso, gentle fan, pleasant temperature.",
        "goal_predicates": {"CurtainsOpen", "CoffeeBrewed", "FanSpeedLow", "LivingLightsOn", "DoorsUnlocked"}
    }
}


def get_default_initial_state() -> Set[str]:
    """Standard midday baseline state of the smart home."""
    return {
        "PowerAvailable",
        "WaterReservoirFull",
        # All hardware devices online by default
        "DeviceOnline_dev1",
        "DeviceOnline_dev2",
        "DeviceOnline_dev3",
        "DeviceOnline_dev4",
        "DeviceOnline_dev5",
        "DeviceOnline_dev6",
        "DeviceOnline_dev7",
        "DeviceOnline_curtains",
        "DeviceOnline_tv",
        "DeviceOnline_strips",
        # Baseline physical states
        "LivingLightsOn",
        "BedroomLampOff",
        "DoorsUnlocked",
        "ClimateCool22",
        "FanSpeedMedium",
        "SecurityDisarmed",
        "CurtainsOpen",
        "TVCinemaOff",
        "CoffeeMakerIdle",
        "AppliancesStandby"
    }


class STRIPSPlanner:
    """Forward State-Space A* Progression Planner with Heuristic Guidance."""

    def __init__(self, actions: Optional[List[Action]] = None):
        self.actions = actions or get_smart_home_domain()

    def heuristic(self, state: Set[str], goals: Set[str]) -> float:
        """Count of unsatisfied goal predicates (admissible goal-counting heuristic)."""
        unsatisfied = goals - state
        return float(len(unsatisfied))

    def solve(
        self,
        initial_state: Set[str],
        goal_predicates: Set[str],
        max_expansions: int = 1000
    ) -> Dict[str, Any]:
        """
        Solves the planning problem via A* search over state space.
        Returns plan action sequence, search statistics, and step-by-step trace.
        """
        # Priority queue holds: (f_score, g_score, state_frozenset, action_path)
        start_state_frozen = frozenset(initial_state)
        goals = set(goal_predicates)

        h0 = self.heuristic(initial_state, goals)
        open_set: List[Tuple[float, float, int, frozenset, List[Action]]] = []
        counter = 0
        heapq.heappush(open_set, (h0, 0.0, counter, start_state_frozen, []))

        g_scores: Dict[frozenset, float] = {start_state_frozen: 0.0}
        nodes_expanded = 0

        while open_set and nodes_expanded < max_expansions:
            f, g, _, current_frozen, path = heapq.heappop(open_set)
            nodes_expanded += 1
            current_state = set(current_frozen)

            # Goal test
            if goals.issubset(current_state):
                return self._build_solution_report(
                    success=True,
                    initial_state=initial_state,
                    goal_predicates=goals,
                    plan=path,
                    nodes_expanded=nodes_expanded
                )

            # Skip if we already found a cheaper route to this state
            if g > g_scores.get(current_frozen, float('inf')):
                continue

            # Expand successors
            for action in self.actions:
                if action.is_applicable(current_state):
                    next_state = action.apply(current_state)
                    next_frozen = frozenset(next_state)
                    tentative_g = g + action.cost

                    if tentative_g < g_scores.get(next_frozen, float('inf')):
                        g_scores[next_frozen] = tentative_g
                        h = self.heuristic(next_state, goals)
                        counter += 1
                        heapq.heappush(
                            open_set,
                            (tentative_g + h, tentative_g, counter, next_frozen, path + [action])
                        )

        # No plan found
        return {
            "success": False,
            "error": "No valid plan found within search horizon.",
            "nodes_expanded": nodes_expanded,
            "unsatisfied_goals": sorted(list(goals - initial_state)),
            "plan": []
        }

    def _build_solution_report(
        self,
        success: bool,
        initial_state: Set[str],
        goal_predicates: Set[str],
        plan: List[Action],
        nodes_expanded: int
    ) -> Dict[str, Any]:
        """Generates detailed step-by-step state transition trace for the plan."""
        trace = []
        running_state = set(initial_state)

        for idx, action in enumerate(plan, 1):
            pre_state = deepcopy(running_state)
            running_state = action.apply(running_state)
            trace.append({
                "step": idx,
                "action": action.name,
                "description": action.description,
                "device_id": action.device_id,
                "preconditions_checked": sorted(list(action.preconditions)),
                "added_effects": sorted(list(action.add_effects)),
                "deleted_effects": sorted(list(action.del_effects)),
                "state_after": sorted(list(running_state))
            })

        return {
            "success": True,
            "plan_length": len(plan),
            "total_cost": sum(a.cost for a in plan),
            "nodes_expanded": nodes_expanded,
            "initial_state": sorted(list(initial_state)),
            "target_goals": sorted(list(goal_predicates)),
            "plan": [a.to_dict() for a in plan],
            "trace": trace
        }

    def replan_on_failure(
        self,
        initial_state: Set[str],
        goal_predicates: Set[str],
        failed_device_id: str = "dev-1"
    ) -> Dict[str, Any]:
        """
        Simulates unexpected device failure during execution and triggers dynamic replanning.
        Example: dev-1 (Living Room Lights) hardware fails -> planner switches to
        TurnOnAmbientAccentStrips fallback or adjusts sequence.
        """
        # 1. Compute original plan
        original_res = self.solve(initial_state, goal_predicates)

        # 2. Simulate hardware fault: remove DeviceOnline predicate
        faulty_state = set(initial_state)
        offline_predicate = f"DeviceOnline_{failed_device_id.replace('-', '')}"
        faulty_state.discard(offline_predicate)

        # 3. Re-run planner
        replan_res = self.solve(faulty_state, goal_predicates)

        return {
            "failed_device": failed_device_id,
            "faulty_predicate_removed": offline_predicate,
            "original_plan": original_res.get("plan", []),
            "original_plan_length": original_res.get("plan_length", 0),
            "replanning_success": replan_res.get("success", False),
            "replanned_plan": replan_res.get("plan", []),
            "replanned_plan_length": replan_res.get("plan_length", 0),
            "replan_trace": replan_res.get("trace", []),
            "explanation": (
                f"Device '{failed_device_id}' went offline. Preconditions requiring {offline_predicate} "
                f"could no longer be satisfied. Planner deduced an alternate path via "
                f"{[a['name'] for a in replan_res.get('plan', [])]}."
                if replan_res.get("success")
                else f"Replanning failed: Goal impossible without {failed_device_id}."
            )
        }
