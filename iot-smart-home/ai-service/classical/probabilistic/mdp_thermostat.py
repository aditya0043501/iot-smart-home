"""
AETHER Classical AI Layer — Markov Decision Process (MDP) with Value Iteration
------------------------------------------------------------------------------
Optimal Thermostat Climate Policy balancing human thermal comfort vs kWh energy cost.

State Space:
  (TemperatureBand, OccupancyState)
  - Temperature Bands: VeryCold (<18°C), Cold (18-21°C), Comfortable (21-24°C), Warm (24-27°C), Hot (>27°C)
  - Occupancy: Occupied, Vacant

Action Space:
  - Heat, Cool, Off

Algorithm:
  Bellman Value Iteration with convergence delta history and optimal policy extraction.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from copy import deepcopy


TEMP_BANDS = ["VeryCold", "Cold", "Comfortable", "Warm", "Hot"]
OCCUPANCIES = ["Occupied", "Vacant"]
ACTIONS = ["Heat", "Cool", "Off"]


class ThermostatMDP:
    """
    Markov Decision Process for Master Climate Thermostat (dev-2).
    """

    def __init__(
        self,
        gamma: float = 0.92,
        epsilon: float = 0.001,
        ambient_outdoor_bias: str = "Hot"  # Typical Chennai warm climate
    ):
        self.gamma = gamma
        self.epsilon = epsilon
        self.outdoor_bias = ambient_outdoor_bias

        # All 10 states
        self.states = [
            (t, occ) for t in TEMP_BANDS for occ in OCCUPANCIES
        ]

        # Transition function T(s, a, s') and Reward function R(s, a, s')
        self.transitions: Dict[Tuple, Dict[Tuple, float]] = {}
        self.rewards: Dict[Tuple, float] = {}
        self._build_model()

    def _build_model(self):
        """Constructs stochastic transitions and multi-objective rewards."""
        # Energy action costs
        ACTION_COSTS = {"Off": 0.0, "Cool": -1.2, "Heat": -1.0}

        # Comfort penalties
        def comfort_reward(t_band: str, occ: str) -> float:
            if occ == "Occupied":
                if t_band == "Comfortable":
                    return 5.0
                elif t_band in ("Cold", "Warm"):
                    return -2.5
                else:  # VeryCold or Hot
                    return -8.0
            else:  # Vacant: comfort is secondary, prioritize energy savings
                if t_band in ("VeryCold", "Hot"):
                    return -1.0  # Mild penalty to prevent extreme structural damage
                return 1.0       # Neutral/positive for saving energy

        for s in self.states:
            t_band, occ = s
            t_idx = TEMP_BANDS.index(t_band)

            for a in ACTIONS:
                s_a = (s, a)
                self.transitions[s_a] = {}

                # 1. Determine next temperature probabilities based on action
                next_t_probs: Dict[str, float] = {}

                if a == "Cool":
                    # Pushes temp down
                    if t_idx == 0:
                        next_t_probs["VeryCold"] = 1.0
                    else:
                        target = TEMP_BANDS[t_idx - 1]
                        next_t_probs[target] = 0.85
                        next_t_probs[t_band] = 0.15

                elif a == "Heat":
                    # Pushes temp up
                    if t_idx == len(TEMP_BANDS) - 1:
                        next_t_probs["Hot"] = 1.0
                    else:
                        target = TEMP_BANDS[t_idx + 1]
                        next_t_probs[target] = 0.85
                        next_t_probs[t_band] = 0.15

                else:  # "Off": drifts toward ambient outdoor temperature
                    if self.outdoor_bias == "Hot":
                        if t_idx < len(TEMP_BANDS) - 1:
                            next_t_probs[TEMP_BANDS[t_idx + 1]] = 0.70
                            next_t_probs[t_band] = 0.30
                        else:
                            next_t_probs["Hot"] = 1.0
                    else:
                        if t_idx > 0:
                            next_t_probs[TEMP_BANDS[t_idx - 1]] = 0.70
                            next_t_probs[t_band] = 0.30
                        else:
                            next_t_probs["VeryCold"] = 1.0

                # 2. Occupancy transition probabilities
                occ_probs = (
                    {"Occupied": 0.85, "Vacant": 0.15}
                    if occ == "Occupied"
                    else {"Vacant": 0.80, "Occupied": 0.20}
                )

                # 3. Combine into joint state transition P(s' | s, a)
                for next_t, p_t in next_t_probs.items():
                    for next_occ, p_occ in occ_probs.items():
                        next_state = (next_t, next_occ)
                        self.transitions[s_a][next_state] = p_t * p_occ

                # 4. Immediate reward = Action cost + Comfort reward
                self.rewards[s_a] = ACTION_COSTS[a] + comfort_reward(t_band, occ)

    def value_iteration(self) -> Dict[str, Any]:
        """
        Runs Bellman Value Iteration until convergence:
        V_{k+1}(s) = max_a [ R(s, a) + gamma * sum_{s'} T(s, a, s') * V_k(s') ]
        """
        # Initialize V(s) = 0 for all states
        V: Dict[Tuple, float] = {s: 0.0 for s in self.states}
        convergence_history = []
        iteration = 0

        while True:
            iteration += 1
            delta = 0.0
            new_V = {}

            for s in self.states:
                # Compute Q-value for each action
                q_values = {}
                for a in ACTIONS:
                    s_a = (s, a)
                    expected_future_val = sum(
                        prob * V[next_s]
                        for next_s, prob in self.transitions[s_a].items()
                    )
                    q = self.rewards[s_a] + self.gamma * expected_future_val
                    q_values[a] = q

                best_val = max(q_values.values())
                new_V[s] = best_val
                delta = max(delta, abs(best_val - V[s]))

            V = new_V
            convergence_history.append({
                "iteration": iteration,
                "delta": round(delta, 5)
            })

            if delta < self.epsilon or iteration >= 200:
                break

        # Extract optimal policy pi*(s) = argmax_a Q(s, a)
        policy: Dict[Tuple, str] = {}
        q_table: Dict[Tuple, Dict[str, float]] = {}

        for s in self.states:
            q_values = {}
            for a in ACTIONS:
                s_a = (s, a)
                expected_future_val = sum(
                    prob * V[next_s]
                    for next_s, prob in self.transitions[s_a].items()
                )
                q_values[a] = round(self.rewards[s_a] + self.gamma * expected_future_val, 3)

            best_action = max(q_values, key=q_values.get)
            policy[s] = best_action
            q_table[s] = q_values

        return {
            "converged": True,
            "total_iterations": iteration,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "convergence_history": convergence_history,
            "value_function": {
                f"{s[0]}_{s[1]}": round(val, 3) for s, val in V.items()
            },
            "optimal_policy": {
                f"{s[0]}_{s[1]}": {
                    "temperature": s[0],
                    "occupancy": s[1],
                    "optimal_action": policy[s],
                    "expected_lifetime_utility": round(V[s], 2),
                    "action_q_values": q_table[s],
                    "justification": self._explain_policy(s, policy[s])
                }
                for s in self.states
            }
        }

    def _explain_policy(self, state: Tuple[str, str], action: str) -> str:
        t, occ = state
        if occ == "Vacant":
            if action == "Off":
                return "Home is vacant: Compressor powered OFF to maximize energy conservation."
            else:
                return f"Home vacant, but temperature ({t}) is extreme: brief {action} to protect property."
        else:
            if t == "Comfortable":
                if action == "Off":
                    return "Temperature is in optimal human comfort band (21-24°C): Passive drift with AC off."
                else:
                    return f"Maintaining comfort band with light {action}."
            elif t in ("Warm", "Hot"):
                return f"Home occupied and warm ({t}): Engaging Cool to restore thermal comfort."
            else:
                return f"Home occupied and cold ({t}): Engaging Heat to restore thermal comfort."
