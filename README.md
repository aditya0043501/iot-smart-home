# AETHER — Smart Home IoT Dashboard & Classical AI Engine

A complete IoT Smart Home Web Application extended with a **Classical Artificial Intelligence Layer** featuring 9 pure Python algorithm implementations (zero external AI library dependencies) operating on a canonical spatial villa topology.

---

## 🌟 Key Features

### 1. Interactive IoT Dashboard
- **Spatial 2D Topology Canvas**: Visualizes the 8-room villa model with real-time status indicators (Safe, Hazard, Unknown, Path).
- **Device Management**: Controls lights, HVAC climate thermostat, motorized smart deadbolt, AeroFlow ceiling fan, and security camera.
- **Real-Time Automation**: Automations for security alerts, eco mode, and preset routines.

### 2. Classical AI Suite (9 From-Scratch Algorithms)
1. **Wumpus-World Hazard Inference Agent** (`ai-service/classical/logic/wumpus.py`):
   - Propositional logic and exact truth-table model checking ($2^8 = 256$ worlds via TT-Entails).
   - Infers Fire, Gas Leak, Water Leak, and Intruder hazards from adjacent room percepts.
2. **STRIPS Automated Planner** (`ai-service/classical/planning/strips.py`):
   - Forward state-space A* progression planner with goal-counting heuristic.
   - Solves routines like "Movie Night", "Leave Home", "Sleep Mode", and dynamically replans when devices fail.
3. **Search Algorithms Comparison & Routing** (`ai-service/classical/search/routing.py`):
   - Side-by-side benchmark of BFS, DFS, UCS, Greedy Best-First, and A* Search.
   - Computes fastest emergency evacuation routes around hazard blockages and complete vacuum coverage tours.
4. **CSP Appliance Scheduler** (`ai-service/classical/csp/scheduler.py`):
   - Backtracking search with Forward Checking (BT-FC), MRV, Degree Heuristic, LCV, and AC-3 Arc Consistency.
   - Schedules high-power appliances under grid peak limits (3.8 kW cap) and mutex load constraints.
5. **Rule-Based Expert System** (`ai-service/classical/logic/expert_system.py`):
   - Forward chaining (data-driven sensor reaction) and Backward chaining (goal-driven root cause diagnostic with AND/OR proof trees).
6. **Bayesian Belief Network** (`ai-service/classical/probabilistic/bayes_net.py`):
   - Exact probabilistic inference by enumeration over a 7-node DAG.
   - Evaluates posterior belief of resident presence $P(\text{ResidentHome} \mid \mathbf{e})$ and intrusion probability $P(\text{Intruder} \mid \mathbf{e})$.
7. **Markov Decision Process (MDP) Thermostat** (`ai-service/classical/probabilistic/mdp_thermostat.py`):
   - Bellman Value Iteration for optimal HVAC temperature policy under stochastic room transitions and comfort-versus-cost trade-offs.
8. **Mamdani Fuzzy Logic Climate Controller** (`ai-service/classical/fuzzy/climate_fuzzy.py`):
   - Fuzzification with triangular and trapezoidal membership functions, min-conjunction rules, and Centroid defuzzification.
9. **Local Search & Evolutionary Optimization** (`ai-service/classical/optimization/energy_opt.py`):
   - Compares Hill Climbing (Steepest Descent), Simulated Annealing, and Genetic Algorithm to minimize 24-hour electricity costs under Time-of-Use tariffs.

---

## 🏗️ Architecture

```
iot-smart-home/
├── index.html                   # Single-Page Application (Tailwind + Lucide + Chart.js)
├── css/
│   └── style.css                # Glassmorphic UI theme & styles
├── js/
│   ├── app.js                   # Main application router and dashboard controller
│   ├── ai-lab.js                # Classical AI Lab visualizer & canvas animator
│   ├── ai-bridge.js             # ML / AI layer bridge
│   ├── charts.js                # Chart rendering helpers
│   ├── store.js                 # Frontend state store
│   └── three-house.js           # 3D villa visualization
├── ai-service/
│   ├── server.py                # Zero-dependency Python HTTP server (Port 8089)
│   ├── main.py                  # FastAPI entrypoint (alternative)
│   ├── classical/               # Pure Python Classical AI Implementations
│   │   ├── graph/               # House graph spatial topology
│   │   ├── logic/               # Wumpus propositional logic & Expert system
│   │   ├── planning/            # STRIPS A* planner
│   │   ├── search/              # BFS, DFS, UCS, Greedy, A* comparison
│   │   ├── csp/                 # Constraint satisfaction scheduler
│   │   ├── probabilistic/       # Bayes Net & MDP Value Iteration
│   │   ├── fuzzy/               # Mamdani Fuzzy Controller
│   │   └── optimization/        # Hill Climbing, SA, Genetic Algorithm
│   ├── evaluation/              # Test suites for all 9 algorithms
│   └── api/                     # REST routes
├── serve.py                     # Static web server for frontend (Port 8088)
├── requirements.txt             # Python dependencies (Optional FastAPI/Uvicorn)
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+ (all classical AI modules use Python Standard Library only)
- Modern web browser (Chrome, Safari, Edge, Firefox)

### 2. Start the Frontend Server
```bash
python3 serve.py
```
Frontend runs on **`http://localhost:8088`**.

### 3. Start the Classical AI Engine
```bash
python3 ai-service/server.py
```
Classical AI server runs on **`http://localhost:8089`**.

---

## 🧪 Running the AI Test Suite

Each algorithm includes an evaluation script in `ai-service/evaluation/`:

```bash
cd ai-service
python3 evaluation/test_wumpus.py
python3 evaluation/test_planning.py
python3 evaluation/test_search.py
python3 evaluation/test_csp.py
python3 evaluation/test_expert_system.py
python3 evaluation/test_bayes.py
python3 evaluation/test_mdp.py
python3 evaluation/test_fuzzy.py
python3 evaluation/test_optimization.py
```

---

## 📄 License
MIT License.
