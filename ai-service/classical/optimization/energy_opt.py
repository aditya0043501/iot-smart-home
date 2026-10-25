"""
AETHER Classical AI Layer — Local Search & Evolutionary Optimization
---------------------------------------------------------------------
Compares 3 optimization algorithms on dynamic-tariff energy load shifting:
  1. Hill Climbing (Steepest-Descent Local Search)
  2. Simulated Annealing (Metropolis criterion with geometric cooling)
  3. Genetic Algorithm (Tournament selection, 2-point crossover, mutation, elitism)

Minimizes 24-hour electricity bill under time-of-use tariffs and peak power limits.
Returns synchronized convergence histories for side-by-side plotting.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
import random
import math
from copy import deepcopy


# 24-hour Time-of-Use (TOU) electricity tariff (INR per kWh)
# Peak: 10:00-14:00 and 18:00-22:00 (₹12.50/kWh)
# Standard: 06:00-10:00, 14:00-18:00, 22:00-24:00 (₹6.50/kWh)
# Off-Peak: 00:00-06:00 (₹3.20/kWh)
HOURLY_TARIFF: List[float] = [
    3.2, 3.2, 3.2, 3.2, 3.2, 3.2,       # 00:00 - 06:00 Off-Peak
    6.5, 6.5, 6.5, 6.5,                 # 06:00 - 10:00 Standard
    12.5, 12.5, 12.5, 12.5,             # 10:00 - 14:00 Peak Solar Noon
    6.5, 6.5, 6.5, 6.5,                 # 14:00 - 18:00 Standard
    12.5, 12.5, 12.5, 12.5,             # 18:00 - 22:00 Peak Evening
    6.5, 6.5                            # 22:00 - 24:00 Standard
]

APPLIANCES_TO_OPTIMIZE: List[Dict[str, Any]] = [
    {"name": "EV_Carport_Charger",  "power_kw": 3.0, "duration_hours": 4},
    {"name": "Storage_Water_Heater","power_kw": 2.0, "duration_hours": 2},
    {"name": "Washing_Machine",     "power_kw": 1.5, "duration_hours": 2},
    {"name": "Smart_Dishwasher",    "power_kw": 1.2, "duration_hours": 2},
    {"name": "Pool_Filter_Pump",    "power_kw": 1.8, "duration_hours": 3},
]

MAX_GRID_KW = 5.0  # Peak allowable whole-home power draw


class EnergyOptimizationProblem:
    """Calculates 24-hour energy costs and peak power penalty."""

    def __init__(
        self,
        tariffs: Optional[List[float]] = None,
        appliances: Optional[List[dict]] = None,
        max_power_kw: float = 5.0
    ):
        self.tariffs = tariffs or HOURLY_TARIFF
        self.appliances = appliances or APPLIANCES_TO_OPTIMIZE
        self.max_power_kw = max_power_kw
        self.num_apps = len(self.appliances)

    def random_schedule(self) -> List[int]:
        """Generates random starting hours for each appliance within legal 24h boundaries."""
        return [
            random.randint(0, 24 - app["duration_hours"])
            for app in self.appliances
        ]

    def evaluate_cost(self, schedule: List[int]) -> Tuple[float, float, float]:
        """
        Computes (total_objective, tariff_cost_inr, penalty_inr).
        Objective = TariffCost + Penalty(Power > MAX_GRID_KW).
        """
        hourly_kw = [0.0] * 24

        for start_t, app in zip(schedule, self.appliances):
            for t in range(start_t, start_t + app["duration_hours"]):
                if t < 24:
                    hourly_kw[t] += app["power_kw"]

        tariff_cost = sum(hourly_kw[t] * self.tariffs[t] for t in range(24))

        # Penalty for exceeding household grid transformer rating
        penalty = 0.0
        for load in hourly_kw:
            if load > self.max_power_kw:
                penalty += 150.0 * ((load - self.max_power_kw) ** 2)

        return (tariff_cost + penalty, tariff_cost, penalty)

    def get_neighbors(self, schedule: List[int]) -> List[List[int]]:
        """Generates 1-hour shift variations for all appliances."""
        neighbors = []
        for i, app in enumerate(self.appliances):
            max_start = 24 - app["duration_hours"]
            current_start = schedule[i]

            if current_start > 0:
                nbr = list(schedule)
                nbr[i] = current_start - 1
                neighbors.append(nbr)

            if current_start < max_start:
                nbr = list(schedule)
                nbr[i] = current_start + 1
                neighbors.append(nbr)

        return neighbors


class OptimizerEngine:
    """Executes Hill Climbing, Simulated Annealing, and Genetic Algorithm."""

    def __init__(self, problem: Optional[EnergyOptimizationProblem] = None):
        self.problem = problem or EnergyOptimizationProblem()

    # ── 1. Hill Climbing (Steepest Descent) ─────────────────────
    def hill_climbing(
        self,
        initial_schedule: Optional[List[int]] = None,
        max_iterations: int = 100
    ) -> Dict[str, Any]:
        curr = initial_schedule or self.problem.random_schedule()
        curr_obj, curr_tariff, curr_pen = self.problem.evaluate_cost(curr)

        history = [{"iteration": 0, "cost": round(curr_obj, 2)}]

        for it in range(1, max_iterations + 1):
            neighbors = self.problem.get_neighbors(curr)
            if not neighbors:
                break

            # Find best neighbor
            best_nbr = None
            best_nbr_obj = curr_obj

            for nbr in neighbors:
                nbr_obj, _, _ = self.problem.evaluate_cost(nbr)
                if nbr_obj < best_nbr_obj:
                    best_nbr_obj = nbr_obj
                    best_nbr = nbr

            if best_nbr is not None and best_nbr_obj < curr_obj:
                curr = best_nbr
                curr_obj = best_nbr_obj
                history.append({"iteration": it, "cost": round(curr_obj, 2)})
            else:
                # Local minimum reached
                history.append({"iteration": it, "cost": round(curr_obj, 2)})
                break

        _, final_tariff, final_pen = self.problem.evaluate_cost(curr)
        return {
            "algorithm": "Hill Climbing",
            "schedule": curr,
            "total_cost": round(curr_obj, 2),
            "tariff_cost_inr": round(final_tariff, 2),
            "penalty_inr": round(final_pen, 2),
            "iterations": len(history) - 1,
            "convergence_history": history
        }

    # ── 2. Simulated Annealing ─────────────────────────────────
    def simulated_annealing(
        self,
        initial_schedule: Optional[List[int]] = None,
        initial_temp: float = 120.0,
        cooling_rate: float = 0.95,
        max_iterations: int = 100
    ) -> Dict[str, Any]:
        curr = initial_schedule or self.problem.random_schedule()
        curr_obj, _, _ = self.problem.evaluate_cost(curr)

        best = list(curr)
        best_obj = curr_obj

        temp = initial_temp
        history = [{"iteration": 0, "cost": round(curr_obj, 2), "temperature": round(temp, 2)}]

        for it in range(1, max_iterations + 1):
            neighbors = self.problem.get_neighbors(curr)
            nbr = random.choice(neighbors)
            nbr_obj, _, _ = self.problem.evaluate_cost(nbr)

            delta = nbr_obj - curr_obj

            # Metropolis acceptance criterion
            if delta < 0 or random.random() < math.exp(-delta / max(temp, 1e-6)):
                curr = nbr
                curr_obj = nbr_obj
                if curr_obj < best_obj:
                    best = list(curr)
                    best_obj = curr_obj

            temp *= cooling_rate
            history.append({
                "iteration": it,
                "cost": round(best_obj, 2),
                "temperature": round(temp, 2)
            })

        _, final_tariff, final_pen = self.problem.evaluate_cost(best)
        return {
            "algorithm": "Simulated Annealing",
            "schedule": best,
            "total_cost": round(best_obj, 2),
            "tariff_cost_inr": round(final_tariff, 2),
            "penalty_inr": round(final_pen, 2),
            "iterations": max_iterations,
            "convergence_history": history
        }

    # ── 3. Genetic Algorithm ───────────────────────────────────
    def genetic_algorithm(
        self,
        population_size: int = 30,
        generations: int = 50,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.18
    ) -> Dict[str, Any]:
        # Initialize population
        population = [self.problem.random_schedule() for _ in range(population_size)]

        def fitness(sched: List[int]) -> float:
            cost, _, _ = self.problem.evaluate_cost(sched)
            return 1.0 / (1.0 + cost)

        history = []
        best_overall = None
        best_overall_cost = float("inf")

        for gen in range(generations + 1):
            # Evaluate fitness of population
            scores = [(sched, self.problem.evaluate_cost(sched)[0], fitness(sched)) for sched in population]
            scores.sort(key=lambda x: x[1])  # Ascending by cost

            gen_best_sched, gen_best_cost, _ = scores[0]

            if gen_best_cost < best_overall_cost:
                best_overall = list(gen_best_sched)
                best_overall_cost = gen_best_cost

            history.append({
                "iteration": gen,
                "cost": round(best_overall_cost, 2),
                "generation": gen
            })

            if gen == generations:
                break

            # Reproduction: Elitism (carry top 2)
            new_pop = [list(scores[0][0]), list(scores[1][0])]

            # Tournament Selection
            def select_parent():
                tournament = random.sample(scores, k=3)
                tournament.sort(key=lambda x: x[1])
                return tournament[0][0]

            while len(new_pop) < population_size:
                p1 = select_parent()
                p2 = select_parent()

                # Crossover
                if random.random() < crossover_rate:
                    cut = random.randint(1, self.problem.num_apps - 1)
                    child = p1[:cut] + p2[cut:]
                else:
                    child = list(p1)

                # Mutation
                for i in range(self.problem.num_apps):
                    if random.random() < mutation_rate:
                        app = self.problem.appliances[i]
                        child[i] = random.randint(0, 24 - app["duration_hours"])

                new_pop.append(child)

            population = new_pop

        _, final_tariff, final_pen = self.problem.evaluate_cost(best_overall)
        return {
            "algorithm": "Genetic Algorithm",
            "schedule": best_overall,
            "total_cost": round(best_overall_cost, 2),
            "tariff_cost_inr": round(final_tariff, 2),
            "penalty_inr": round(final_pen, 2),
            "iterations": generations,
            "convergence_history": history
        }

    def compare_all(self, seed_schedule: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Runs Hill Climbing, Simulated Annealing, and GA on identical energy problem.
        Returns synchronized convergence curves and comparative savings breakdown.
        """
        seed = seed_schedule or [8, 12, 11, 19, 18]  # Unoptimized peak-hour schedule
        unoptimized_cost, unopt_tariff, unopt_pen = self.problem.evaluate_cost(seed)

        hc_res = self.hill_climbing(initial_schedule=list(seed))
        sa_res = self.simulated_annealing(initial_schedule=list(seed))
        ga_res = self.genetic_algorithm(population_size=30, generations=60)

        # Build detailed appliance schedule mapping for the winner
        winner = min([hc_res, sa_res, ga_res], key=lambda x: x["total_cost"])

        best_schedule_map = []
        for start_t, app in zip(winner["schedule"], self.problem.appliances):
            best_schedule_map.append({
                "appliance": app["name"],
                "power_kw": app["power_kw"],
                "duration_hours": app["duration_hours"],
                "start_hour": f"{start_t:02d}:00",
                "end_hour": f"{(start_t + app['duration_hours']):02d}:00",
                "scheduled_tariff": HOURLY_TARIFF[start_t]
            })

        return {
            "unoptimized_baseline": {
                "schedule": seed,
                "total_cost_inr": round(unoptimized_cost, 2),
                "tariff_cost_inr": round(unopt_tariff, 2),
                "penalty_inr": round(unopt_pen, 2)
            },
            "comparison": [
                {
                    "algorithm": hc_res["algorithm"],
                    "final_cost_inr": hc_res["total_cost"],
                    "savings_percent": round((1 - hc_res["total_cost"] / max(unoptimized_cost, 1e-3)) * 100, 1),
                    "tariff_component": hc_res["tariff_cost_inr"],
                    "penalty_component": hc_res["penalty_inr"],
                    "steps": hc_res["iterations"]
                },
                {
                    "algorithm": sa_res["algorithm"],
                    "final_cost_inr": sa_res["total_cost"],
                    "savings_percent": round((1 - sa_res["total_cost"] / max(unoptimized_cost, 1e-3)) * 100, 1),
                    "tariff_component": sa_res["tariff_cost_inr"],
                    "penalty_component": sa_res["penalty_inr"],
                    "steps": sa_res["iterations"]
                },
                {
                    "algorithm": ga_res["algorithm"],
                    "final_cost_inr": ga_res["total_cost"],
                    "savings_percent": round((1 - ga_res["total_cost"] / max(unoptimized_cost, 1e-3)) * 100, 1),
                    "tariff_component": ga_res["tariff_cost_inr"],
                    "penalty_component": ga_res["penalty_inr"],
                    "steps": ga_res["iterations"]
                }
            ],
            "winning_algorithm": winner["algorithm"],
            "optimal_schedule": best_schedule_map,
            "convergence_curves": {
                "hill_climbing": hc_res["convergence_history"],
                "simulated_annealing": sa_res["convergence_history"],
                "genetic_algorithm": ga_res["convergence_history"]
            }
        }
