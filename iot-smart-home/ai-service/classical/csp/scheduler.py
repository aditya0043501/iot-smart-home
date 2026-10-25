"""
AETHER Classical AI Layer — Constraint Satisfaction Problem (CSP) Appliance Scheduler
-------------------------------------------------------------------------------------
Implements:
  - Backtracking Search with Forward Checking (BT-FC)
  - Minimum Remaining Values (MRV) variable selection heuristic
  - Degree Heuristic (tie-breaker for MRV)
  - Least Constraining Value (LCV) value ordering heuristic
  - AC-3 Arc Consistency constraint propagation

Solves smart home appliance scheduling under:
  - Total peak grid power cap (e.g. max 3.5 kW)
  - Mutex constraints: no two heavy loads running concurrently
  - Appliance run durations and user completion deadlines
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from copy import deepcopy


class ApplianceVariable:
    """An appliance that needs to be scheduled for a continuous duration."""

    def __init__(
        self,
        name: str,
        power_watts: float,
        duration_slots: int,
        earliest_start: int,
        deadline: int,
        is_heavy_load: bool = False,
        description: str = ""
    ):
        self.name = name
        self.power_watts = power_watts
        self.duration_slots = duration_slots
        self.earliest_start = earliest_start
        self.deadline = deadline
        self.is_heavy_load = is_heavy_load
        self.description = description

        # Initial domain: all possible start slots such that start + duration <= deadline
        self.initial_domain = [
            t for t in range(earliest_start, deadline - duration_slots + 1)
        ]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "power_watts": self.power_watts,
            "duration_slots": self.duration_slots,
            "earliest_start": self.earliest_start,
            "deadline": self.deadline,
            "is_heavy_load": self.is_heavy_load,
            "description": self.description,
            "domain_size": len(self.initial_domain),
            "initial_domain": self.initial_domain
        }


def get_default_appliances() -> Dict[str, ApplianceVariable]:
    """Canonical household appliance scheduling profile."""
    return {
        "EV_Carport_Charger": ApplianceVariable(
            name="EV_Carport_Charger",
            power_watts=2800.0,
            duration_slots=3,
            earliest_start=0,
            deadline=8,
            is_heavy_load=True,
            description="Level-2 EV Carport Charger in Garage (dev-car)"
        ),
        "Water_Heater": ApplianceVariable(
            name="Water_Heater",
            power_watts=2000.0,
            duration_slots=2,
            earliest_start=0,
            deadline=7,
            is_heavy_load=True,
            description="Central Solar/Grid Domestic Water Heater"
        ),
        "Washing_Machine": ApplianceVariable(
            name="Washing_Machine",
            power_watts=1400.0,
            duration_slots=2,
            earliest_start=1,
            deadline=9,
            is_heavy_load=False,
            description="Smart Laundry Washing Machine"
        ),
        "Smart_Dishwasher": ApplianceVariable(
            name="Smart_Dishwasher",
            power_watts=1200.0,
            duration_slots=2,
            earliest_start=2,
            deadline=10,
            is_heavy_load=False,
            description="Kitchen Eco Dishwasher"
        ),
        "Smart_Convection_Oven": ApplianceVariable(
            name="Smart_Convection_Oven",
            power_watts=2100.0,
            duration_slots=1,
            earliest_start=6,
            deadline=11,
            is_heavy_load=True,
            description="Kitchen Smart Convection Oven (dev-8)"
        ),
    }


class ApplianceCSPSolver:
    """
    Constraint Satisfaction Solver for Smart Grid Demand-Response.
    Finds collision-free, power-capped appliance schedules.
    """

    def __init__(
        self,
        appliances: Optional[Dict[str, ApplianceVariable]] = None,
        power_cap_watts: float = 3800.0,
        total_horizon_slots: int = 12
    ):
        self.appliances = appliances or get_default_appliances()
        self.power_cap_watts = power_cap_watts
        self.total_horizon = total_horizon_slots
        self.backtrack_count = 0
        self.assignments_count = 0
        self.search_tree_trace: List[dict] = []

    def _intervals_overlap(self, start1: int, dur1: int, start2: int, dur2: int) -> bool:
        """Tests whether two appliance runtime windows overlap in time."""
        return max(start1, start2) < min(start1 + dur1, start2 + dur2)

    def is_consistent_assignment(
        self,
        var_name: str,
        start_slot: int,
        current_assignment: Dict[str, int]
    ) -> Tuple[bool, str]:
        """
        Validates constraints:
          1. No two heavy loads overlap concurrently.
          2. Aggregate wattage in any shared slot does not exceed power_cap_watts.
        """
        app = self.appliances[var_name]

        # Check overlapping active appliances across all hours of var_name's run
        var_slots = set(range(start_slot, start_slot + app.duration_slots))

        # Build load profile with candidate assignment
        hourly_load: Dict[int, float] = {t: 0.0 for t in range(self.total_horizon)}
        for t in var_slots:
            hourly_load[t] += app.power_watts

        for other_name, other_start in current_assignment.items():
            other_app = self.appliances[other_name]

            # Mutex heavy load check
            if app.is_heavy_load and other_app.is_heavy_load:
                if self._intervals_overlap(start_slot, app.duration_slots, other_start, other_app.duration_slots):
                    return (
                        False,
                        f"Heavy Load Conflict: {var_name} ({app.power_watts}W) and "
                        f"{other_name} ({other_app.power_watts}W) cannot run concurrently."
                    )

            # Accumulate power
            for t in range(other_start, other_start + other_app.duration_slots):
                if t < self.total_horizon:
                    hourly_load[t] += other_app.power_watts
                    if hourly_load[t] > self.power_cap_watts:
                        return (
                            False,
                            f"Power Cap Exceeded: Combined load at slot {t} is {hourly_load[t]}W "
                            f"(Cap: {self.power_cap_watts}W)."
                        )

        return True, "Consistent"

    # ── AC-3 Arc Consistency ───────────────────────────────────
    def ac3(self, domains: Dict[str, List[int]]) -> Tuple[bool, List[dict]]:
        """
        AC-3 Algorithm: Prunes values that violate pairwise binary constraints.
        Returns (is_consistent, pruning_trace).
        """
        trace = []
        # Arcs between all pairs of variables
        queue = []
        var_list = list(self.appliances.keys())
        for i in range(len(var_list)):
            for j in range(len(var_list)):
                if i != j:
                    queue.append((var_list[i], var_list[j]))

        while queue:
            xi, xj = queue.pop(0)
            revised, pruned_values = self._revise(xi, xj, domains)

            if revised:
                trace.append({
                    "arc": f"({xi} -> {xj})",
                    "pruned_values": pruned_values,
                    "remaining_domain": list(domains[xi])
                })
                if not domains[xi]:
                    return False, trace  # Domain wiped out: unsolvable

                for xk in var_list:
                    if xk != xi and xk != xj:
                        queue.append((xk, xi))

        return True, trace

    def _revise(
        self,
        xi: str,
        xj: str,
        domains: Dict[str, List[int]]
    ) -> Tuple[bool, List[int]]:
        """Prunes any start slot in domain[xi] that has no consistent counterpart in domain[xj]."""
        revised = False
        pruned = []
        remaining = []

        for val_i in domains[xi]:
            # Is there any val_j in domain[xj] compatible with val_i?
            has_support = False
            for val_j in domains[xj]:
                is_ok, _ = self.is_consistent_assignment(xi, val_i, {xj: val_j})
                if is_ok:
                    has_support = True
                    break

            if has_support:
                remaining.append(val_i)
            else:
                revised = True
                pruned.append(val_i)

        if revised:
            domains[xi] = remaining

        return revised, pruned

    # ── Variable & Value Heuristics (MRV, Degree, LCV) ────────
    def _select_unassigned_variable(
        self,
        assignment: Dict[str, int],
        domains: Dict[str, List[int]]
    ) -> str:
        """
        Selects next variable using:
          1. Minimum Remaining Values (MRV): fewest legal values in domain.
          2. Degree Heuristic (tie-breaker): involved in most constraints with unassigned variables.
        """
        unassigned = [v for v in self.appliances.keys() if v not in assignment]

        def var_key(v: str) -> Tuple[int, int]:
            domain_size = len(domains[v])
            # Degree: count how many other unassigned variables are heavy loads
            degree = sum(
                1 for u in unassigned
                if u != v and (self.appliances[v].is_heavy_load and self.appliances[u].is_heavy_load)
            )
            return (domain_size, -degree)

        return min(unassigned, key=var_key)

    def _order_domain_values(
        self,
        var_name: str,
        domains: Dict[str, List[int]],
        assignment: Dict[str, int]
    ) -> List[int]:
        """
        Least Constraining Value (LCV) heuristic:
        Prefers values that eliminate the fewest choices for unassigned neighbors.
        """
        unassigned = [v for v in self.appliances.keys() if v not in assignment and v != var_name]

        def count_conflicts(val: int) -> int:
            conflicts = 0
            for u in unassigned:
                for u_val in domains[u]:
                    is_ok, _ = self.is_consistent_assignment(var_name, val, {u: u_val})
                    if not is_ok:
                        conflicts += 1
            return conflicts

        return sorted(domains[var_name], key=count_conflicts)

    # ── Backtracking Search with Forward Checking (BT-FC) ──────
    def solve(self, use_ac3: bool = True) -> Dict[str, Any]:
        """
        Executes complete CSP solver with AC-3 preprocessing and BT-FC.
        Returns final schedule, backtrack count, power curve, and search trace.
        """
        self.backtrack_count = 0
        self.assignments_count = 0
        self.search_tree_trace = []

        domains = {
            name: list(app.initial_domain)
            for name, app in self.appliances.items()
        }

        ac3_trace = []
        if use_ac3:
            consistent, ac3_trace = self.ac3(domains)
            if not consistent:
                return {
                    "success": False,
                    "error": "AC-3 detected unsolvable domain constraints prior to search.",
                    "ac3_trace": ac3_trace
                }

        solution_assignment: Dict[str, int] = {}
        success = self._backtrack({}, domains, solution_assignment)

        if not success:
            return {
                "success": False,
                "error": "No valid schedule satisfies all power caps and deadlines.",
                "backtrack_count": self.backtrack_count,
                "assignments_evaluated": self.assignments_count,
                "trace": self.search_tree_trace
            }

        # Calculate final hourly power profile
        hourly_schedule: Dict[int, List[dict]] = {t: [] for t in range(self.total_horizon)}
        hourly_power: Dict[int, float] = {t: 0.0 for t in range(self.total_horizon)}

        for name, start_t in solution_assignment.items():
            app = self.appliances[name]
            for t in range(start_t, start_t + app.duration_slots):
                if t < self.total_horizon:
                    hourly_power[t] += app.power_watts
                    hourly_schedule[t].append({
                        "appliance": name,
                        "power_watts": app.power_watts,
                        "slot_of_run": t - start_t + 1,
                        "total_duration": app.duration_slots
                    })

        return {
            "success": True,
            "power_cap_watts": self.power_cap_watts,
            "horizon_slots": self.total_horizon,
            "schedule": {
                name: {
                    "start_slot": start,
                    "end_slot": start + self.appliances[name].duration_slots,
                    "power_watts": self.appliances[name].power_watts,
                    "duration_slots": self.appliances[name].duration_slots,
                    "description": self.appliances[name].description
                }
                for name, start in sorted(solution_assignment.items(), key=lambda x: x[1])
            },
            "hourly_load_profile": [
                {
                    "hour": f"T+{t:02d}:00",
                    "total_watts": round(hourly_power[t], 1),
                    "active_appliances": [a["appliance"] for a in hourly_schedule[t]],
                    "capacity_headroom": round(self.power_cap_watts - hourly_power[t], 1)
                }
                for t in range(self.total_horizon)
            ],
            "solver_metrics": {
                "backtrack_count": self.backtrack_count,
                "assignments_evaluated": self.assignments_count,
                "ac3_pruned_arcs": len(ac3_trace),
                "peak_power_watts": max(hourly_power.values()) if hourly_power else 0.0
            },
            "ac3_trace": ac3_trace,
            "search_tree_trace": self.search_tree_trace[:50]  # Cap for clean JSON
        }

    def _backtrack(
        self,
        assignment: Dict[str, int],
        domains: Dict[str, List[int]],
        solution_out: Dict[str, int]
    ) -> bool:
        """Recursive BT-FC solver with MRV and LCV."""
        if len(assignment) == len(self.appliances):
            solution_out.update(assignment)
            return True

        var_name = self._select_unassigned_variable(assignment, domains)
        ordered_values = self._order_domain_values(var_name, domains, assignment)

        for val in ordered_values:
            self.assignments_count += 1
            is_ok, reason = self.is_consistent_assignment(var_name, val, assignment)

            self.search_tree_trace.append({
                "assignment_num": self.assignments_count,
                "variable": var_name,
                "tried_slot": val,
                "is_consistent": is_ok,
                "reason": reason,
                "current_backtracks": self.backtrack_count
            })

            if is_ok:
                assignment[var_name] = val
                saved_domains = deepcopy(domains)

                # --- Forward Checking ---
                # Prune impossible values from remaining unassigned variables
                forward_ok = True
                unassigned = [v for v in self.appliances if v not in assignment]
                for other in unassigned:
                    domains[other] = [
                        other_val for other_val in domains[other]
                        if self.is_consistent_assignment(other, other_val, assignment)[0]
                    ]
                    if not domains[other]:
                        forward_ok = False
                        break

                if forward_ok:
                    if self._backtrack(assignment, domains, solution_out):
                        return True

                # Backtrack
                self.backtrack_count += 1
                del assignment[var_name]
                domains = saved_domains

        return False
