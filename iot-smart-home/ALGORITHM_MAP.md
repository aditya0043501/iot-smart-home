# Algorithm Map (real status, Batch 0)

Each brief row (section 3) is mapped to the code that exists today. "Measured" means a number produced by the evaluation suite. Nothing in the repo is measured against a baseline yet, except the guard's timing.

| # | Brief component | Existing code | Status | Baseline implemented? | Measured vs baseline | Batch |
|---|---|---|---|---|---|---|
| 1 | Guard: threshold + debounce + hysteresis | `core/guard.py` | SG-04 live, edge-triggered. No debounce or hysteresis yet. | n/a (safety floor) | evaluate() median 4.1 µs (timing only) | B3 |
| 2 | Rule engine, forward chaining + trace | `classical/logic/expert_system.py` | Forward and backward chaining work. Facts can now come from device state (`DeviceStateStore.expert_facts()`). No stored trace per firing. | No | Not measured | B3 |
| 3 | EWMA / Z-score spike detector | none (the `/api/simulate/*` rows fake a score) | Missing | No | Run evaluation to fill | B4 |
| 4 | Isolation Forest | none (named in `/api/ai/status`, not implemented) | Missing | No | Run evaluation to fill | B4 |
| 5 | XGBoost energy forecast | `/api/forecast/energy` heuristic only | Missing | No | Run evaluation to fill | B4 |
| 6 | Occupancy: profile + Bayesian presence | `classical/probabilistic/bayes_net.py`: a 7-node net with exact enumeration and hand-set CPTs, no time filter | Partial (can be reused) | No | Not measured | B4 |
| 7 | CSP load scheduler + branch and bound | `classical/csp/scheduler.py`: BT-FC, MRV, degree, LCV, AC-3. Finds a feasible schedule but has **no cost objective**. | Partial | No | Not measured | B5 |
| 8 | Comfort controller (bang-bang vs ≤2 candidates) | `classical/fuzzy/climate_fuzzy.py` (Mamdani). No RC thermal model, no bang-bang, no PID. | Partial | No | Not measured | B5 |
| 9 | Sensor-gap hazard inference | `classical/logic/wumpus.py`: truth-table model checking over the room graph | Partial (can be reused) | No | Not measured | B6 |
| 10 | Evacuation routing | `classical/search/routing.py`, A* on the room graph | Partial (A* reusable) | No | Not measured | B6 |
| 11 | Scene executor | `classical/planning/strips.py`, a full STRIPS A* planner | To be replaced by topological sort + preconditions | No | Not measured | B7 |
| 12 | LLM function calling | `llm/` empty; `.env.example` mentions OpenAI only | Missing | No | n/a | B8 |

## Existing code the brief marks "NOT in the product"

These all work and pass their own tests today. The brief says to remove them from the app, or move them to `docs/teaching_notebooks/` if wanted for teaching. Pending approval: D-003.

| Code | What it is | Used by |
|---|---|---|
| `classical/search/routing.py` (BFS/DFS/UCS/Greedy comparison, vacuum coverage tour) | Search benchmark | `/api/classical/search/compare`, `/search/vacuum`, AI Lab card |
| `classical/optimization/energy_opt.py` | Hill climbing, simulated annealing, genetic algorithm | `/api/classical/optimization/*`, AI Lab card |
| `classical/probabilistic/mdp_thermostat.py` | MDP value iteration | `/api/classical/mdp/solve`, AI Lab card |
| `classical/planning/strips.py` (full STRIPS) | A* planner | `/api/classical/planning/*`, AI Lab card |
| Wumpus "autonomous patrol" in `wumpus.py` | Agent walk-through | `/api/classical/wumpus/simulate` |
| K-Means and Q-Learning | Only named in `/api/ai/status`, no code | Status endpoint only |
