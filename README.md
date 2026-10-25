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
MIT License


ROLE
You are a principal engineer on an IoT + applied-AI team extending an EXISTING project, "Sentient Home". Do not rewrite it and do not break working features. I am the architect; you implement. I do NOT have hardware connected and will not for now. The system must be fully buildable, testable and demoable with zero physical devices, AND it must have a clear, tested path to real hardware so that adding a board later is a flashing-and-configuration task, not a redesign.

EXISTING STATE (verify by reading the repo first)
- Backend: FastAPI, SQLAlchemy + SQLite, WebSocket live state, event bus, device registry, deterministic safety guard (rules SG-xx), simulator with scenario injection, 30 days of seeded history.
- Hardware layer already in-process: MQTT transport, adapter registry, HA-discovery topic scheme, /hardware/test bench endpoint. No firmware, no broker config, no wiring docs.
- Frontend: zero-build vanilla ES modules, 9 views, API client and WebSocket hook. Keep it.
- AI: ai/ml, ai/classical, ai/evaluation are unbuilt; endpoints return HTTP 501 with a DecisionArtifact contract the UI already renders. Do not change that contract.
- Runtime is Python 3.12. No Docker assumed.
- Known bugs: window_open_ac_on room flag vs device state mismatch (alert never raised); sim clock drift at 600x; stale ARCHITECTURE.md and ALGORITHM_MAP.md.

==================================================
1. ENGINEERING PRINCIPLES
==================================================
P1. Hardware-ready, not hardware-bound. All device I/O goes through one interface. Simulated, fake-MQTT and real devices are interchangeable implementations of it.
P2. Practicality gate. Every algorithm must beat a stated simple baseline on a measured number, in the evaluation suite. If it does not, delete it from the product, record why in docs/DECISIONS.md, and ship the baseline. A deleted algorithm with an honest note is a good outcome; a decorative algorithm is a failure.
P3. Safety is deterministic. Gas, smoke, flame, flood, locks, mains-level loads are decided only by the rule guard. ML, fuzzy, planner and LLM output can advise, or act on non-critical actuators only.
P4. Honest data. Every reading carries source = simulated | fake_node | real. The UI badges it. Any metric computed on simulated data is labelled "simulated" everywhere it appears.
P5. Every claim of "works" comes from a test or a measured number. Unknown means "run evaluation to fill". No invented metrics.
P6. Secrets only in .env. Tell me about any new dependency or paid service before adding it.
P7. Tests finish in under 10 seconds each. No sleep loops; use an injectable clock.
P8. Every algorithm file gets the standard header (ALGO, CATEGORY, WHAT, WHY HERE, WHERE USED, INPUT, OUTPUT, HOW IT WORKS, BASELINE, EFFICIENCY, LIMITS, JUDGE Q&A), numbered STEP comments and an "ALGO-ENTRY: <name>" tag. EFFICIENCY uses only measured numbers.

==================================================
2. TARGET ARCHITECTURE (ports and adapters)
==================================================
Layers, top to bottom:
  UI (existing SPA)
  API + WebSocket
  Application services: command pipeline, rule engine, scene executor, AI services
  Domain core: device model, room graph, state store, event bus, safety guard
  PORTS (interfaces): DeviceTransport, Clock, TelemetryStore, LLMProvider
  ADAPTERS: SimTransport | MqttTransport (to Mosquitto) | FakeNode (real MQTT, no board) | future real ESP32 nodes

DeviceTransport interface (define it explicitly, one file, with a docstring contract):
  subscribe_state(callback), send_command(device, cmd, cmd_id, expiry) -> Ack, availability events, health().
Every adapter must pass the SAME conformance test suite (tests/conformance/). A real board is accepted only by passing that suite plus hardware/tools/bench_test.py.

MQTT contract (extend the existing HA-discovery scheme, do not replace):
  sh/{home}/{room}/{device}/state  retained JSON: ts, seq, source, fw_version, rssi, values{}
  sh/{home}/{room}/{device}/cmd    QoS1 JSON: cmd_id, expiry, action, params
  sh/{home}/{room}/{device}/ack    echoes cmd_id, result, latency
  sh/{home}/{room}/{device}/avail  LWT online/offline
  sh/{home}/_system/alerts         guard and AI alerts
Payloads validated by pydantic, unknown fields rejected, stale timestamps rejected, duplicate seq dropped.

Reference node types (used for fake nodes now, real boards later):
| Node | Signals | Actuators |
|---|---|---|
| env | temperature, humidity, motion (PIR), light | none |
| safety | smoke/LPG gas, air quality, flood, flame | buzzer |
| access | door reed, window reed, lock state | lock servo (demo) |
| power | volts, amps, watts, kWh | relay |
| actuate | on/off/dim state | relay channels, IR for AC |

Simulator must model physics well enough to evaluate controllers: first-order (RC) thermal model per room with outdoor temperature, window-open heat loss, AC capacity and compressor short-cycle limits; per-appliance power profiles; time-of-use tariff table; occupancy routines; sensor noise, drift and fault injection. Parameters live in config, not code.

==================================================
3. ALGORITHM DECISIONS (the contract for what ships)
==================================================
Each row: what it does for a real home, the baseline it must beat, and the delete rule.

| # | Component | Practical job | Where it runs | Baseline | Pass criterion | If it fails |
|---|---|---|---|---|---|---|
| 1 | Threshold + debounce + hysteresis (guard) | Instant gas/smoke/flood/flame/window+AC response | Edge firmware later, backend guard now | none, this is the safety floor | Test matrix passes: hazard x device state x network condition | Not optional |
| 2 | Rule engine, forward chaining with fired-rule trace | User automations plus "why did this fire?" answers from the trace | Backend | Hard-coded if/else automations | Same behaviour as baseline plus a trace for every action | Keep, it is the audit trail |
| 3 | EWMA / Z-score spike detector | Power spikes, stuck or drifting sensors | Edge later, backend now | Fixed wattage threshold | Higher F1 on injected faults at equal false-alarm rate | Ship fixed threshold only |
| 4 | Isolation Forest | Multivariate oddities EWMA misses (e.g. normal power but abnormal power-vs-temperature relation) | Backend | EWMA from row 3 | Improves F1 or detection delay by a margin written in advance, on faults EWMA misses | Ship EWMA only |
| 5 | XGBoost energy forecast | Next-24h kWh and cost, input to scheduling | Backend | Same hour yesterday AND same hour last week | Lower MAE than the better baseline on a time-based holdout | Ship the baseline forecast |
| 6 | Occupancy: hour-of-week profile + Bayesian presence filter (exact enumeration) | P(home) from PIR, door events, time prior; drives away mode and preheating | Backend | PIR with a fixed timeout | Higher accuracy and fewer false "away" flips on simulated labels | Ship PIR timeout |
| 7 | CSP load scheduler (backtracking, forward checking, MRV, AC-3) with cost objective via branch and bound | Shift dishwasher/washer/EV-style loads under a power cap and tariff | Backend | Run every load at its preferred time | Lower daily cost with zero constraint violations | Ship preferred-time schedule |
| 8 | Comfort controller: hysteresis baseline vs PID with minimum on/off times vs fuzzy | Fewer AC compressor starts, less overshoot | Backend, firmware later | Bang-bang with 0.7 K hysteresis | Fewer starts per hour AND comfort violation not worse AND energy not higher. Implement at most two candidates, ship the winner, delete the loser | Ship bang-bang |
| 9 | Sensor-gap hazard inference (propositional model checking over the room graph) | Infer likely hazard in rooms WITHOUT a sensor from sensed neighbours | Backend | "Neighbour exceeded threshold, so room is unsafe" rule | Lower false-safe rate or earlier detection on scenarios with unsensed rooms | Delete; ship the neighbour rule |
| 10 | Evacuation routing (A* or Dijkstra, hazard-weighted edges) | Exit route avoiding hazard rooms | Backend | Shortest path ignoring hazards | Route avoids all hazard rooms when a safe route exists | Keep, it is cheap and correct |
| 11 | Scene executor: preconditions, dependency ordering (topological sort), offline-device fallback, ack-driven retry | "Movie night", "leave home", "sleep mode" reliably executed in a valid order | Backend | Fixed command list fired blindly | Higher scene success rate when devices are offline or in a bad state | Ship the fixed list |
| 12 | LLM function calling (Gemini, Groq, OpenRouter :free models, Ollama, rule-based parser) | Natural-language control, explanations built from tool results, JSON automation drafts | Backend | Rule-based intent parser | Parses open-ended commands the rule parser cannot, with 100% schema-valid or rejected output | Keep the rule parser as the floor |

Explicitly NOT in the product: BFS/DFS/Greedy/UCS comparisons, robot-vacuum coverage, hill climbing, simulated annealing, genetic algorithm, MDP, full STRIPS, Q-learning, autoencoders, K-Means routines. If I ask for a teaching demo of any of them, put it in /docs/teaching_notebooks/, never in the app.

==================================================
4. BATCHES (stop and wait for my approval after each)
==================================================
BATCH 0: BASELINE AND BUGS
- Write CURRENT_STATE.md: what runs, what is 501, test coverage, how to start.
- Fix the window state mismatch (device state is the single source of truth; room flag derived; SG-04 raises an alert). Add an injectable Clock; clamp or reset sim speed for reproducible scenarios.
- Refresh ARCHITECTURE.md and ALGORITHM_MAP.md to real status. Create docs/DECISIONS.md.
Acceptance: pytest passes; a test proves window_open_ac_on raises an alert.

BATCH 1: DEVICE PORT, CONTRACT, FAKE NODES
- Define DeviceTransport and the pydantic payload schemas. Refactor Sim and Mqtt adapters onto the interface without changing behaviour.
- hardware/mosquitto/: mosquitto.conf, per-device credential script, optional TLS switch. If Mosquitto is not installable here, add an in-process broker shim with identical topic semantics and mark it clearly.
- hardware/tools/fake_node.py: emulates all 5 node types over real MQTT (publishes state, obeys cmd with ack, LWT on exit, injectable faults and latency).
- tests/conformance/: one suite every adapter must pass (state schema, cmd/ack round trip, expiry, idempotency by cmd_id, LWT availability, stale and duplicate rejection).
- UI: per-device badge "simulated / fake node / live hardware" and online/offline from LWT.
Acceptance: all adapters pass conformance; 5 fake nodes appear online/offline on the dashboard.

BATCH 2: DATA QUALITY AND SOURCE SWITCH
- Per-device config: source = simulated | fake_node | real. All sources flow through the same bus and tables, tagged.
- Quality checks: out of range, stuck sensor, stale, duplicate seq. Quarantine and log, never silently drop.
- Telemetry store with the retention and indexes the ML needs.
Acceptance: switching a device's source changes no downstream code path; quality-check tests pass.

BATCH 3: SAFETY GUARD AND COMMAND PIPELINE (rows 1, 2)
- Guard rules for gas, smoke, flame, flood, window+AC, door/lock, each with test vectors.
- Command pipeline: validate, guard, rate limit, publish with cmd_id, await ack, retry with backoff, mark degraded after N failures. Define and document the fail-safe state of every actuator on broker loss.
- Rule engine with forward chaining and a stored trace per firing. "Why is the alarm on?" is answered by reading the trace, not by a separate algorithm.
- Locks and alarms need explicit UI confirmation and are never actuated by ML, fuzzy, planner or LLM output alone.
Acceptance: hazard x device-state x network-condition matrix passes.

BATCH 4: ML (rows 3 to 6)
- Anomaly: EWMA baseline and Isolation Forest; label fault windows from the simulator injection log; report precision, recall, F1 and detection delay for both on identical labels, including a set of faults designed to defeat a simple threshold.
- Forecast: XGBoost with hour, weekday, outdoor temp and occupancy; time-based split; MAE/RMSE against both baselines.
- Occupancy: hour-of-week profile plus Bayesian presence filter vs PIR timeout. State in LIMITS that labels are simulator-derived.
- Apply the pass criteria from section 3. Delete losers and log them in DECISIONS.md.
- Each module: train(), predict(), explain(), artifact, metrics into evaluation_reports, DecisionArtifact output.
Acceptance: metrics visible in the UI with a "simulated" label; a spike injected through a fake node is flagged with its top contributing signal.

BATCH 5: OPTIMISATION AND COMFORT (rows 7, 8)
- CSP scheduler consuming the forecast and tariff table; exact cost optimum; report cost vs preferred-time baseline and constraint violations (must be zero).
- Comfort controller: implement baseline plus at most two candidates against the RC thermal model on the same recorded temperature and weather traces; report compressor starts per hour, comfort violation (degree-hours outside the band) and energy.
- Each returns a step trace for the AI Lab card.
Acceptance: numbers in evaluation_reports; losing controller removed.

BATCH 6: HAZARD INFERENCE AND EVACUATION (rows 9, 10)
- Build scenarios where some rooms have no sensor. Implement the neighbour-threshold baseline first, then propositional inference. Compare false-safe rate and time to detect.
- Evacuation: hazard-weighted shortest path to the nearest exit with verdicts from row 9 (or the baseline if row 9 is deleted).
- Decide by the pass criterion and record the outcome in DECISIONS.md.
Acceptance: either the inference module ships with measured gain, or it is deleted with the reason recorded.

BATCH 7: SCENE EXECUTOR (row 11)
- Scenes defined as goals with preconditions and effects per device action; resolve order with a topological sort; substitute or skip when a device is offline; verify with acks; roll back or report partial completion.
- Evaluate against a fixed blind command list across scenarios with offline and wrong-state devices.
Acceptance: measured scene success rate and a visible plan with per-step result in the UI.

BATCH 8: LLM LAYER (row 12)
- Provider chain: Gemini, Groq, OpenRouter (:free models only), Ollama, rule-based parser. Call ListModels to verify real model names before hardcoding; verify current free-tier terms and tell me anything needing a card.
- Function calling maps only to the existing command API; validate every output against a JSON schema; cache, rate limit, backoff; per-response provider badge.
- Chat control, insights built only from tool results (never invented numbers), automation drafts as JSON with preview and confirm, alert explanations from guard and anomaly output.
Acceptance: with no keys and no network, about ten intents still work; schema-violating output is rejected in tests.

BATCH 9: HARDWARE PATHWAY PACKAGE (documentation and compile-only code, nothing flashed)
- hardware/firmware/: PlatformIO project, shared library (WiFi, MQTT, schema, NTP, watchdog, OTA-ready, offline buffer with seq numbers), one env per node type, edge logic: debounce/hysteresis safety latch that works with no network, EWMA filter. Credentials in a git-ignored config template. It must COMPILE in CI and its edge logic must pass native unit tests; it is not flashed or tested on a board.
- hardware/docs/HARDWARE.md: bill of materials with approximate prices, wiring table per node (pin, sensor pin, voltage, level shifter or resistor notes), power budget, MQ-sensor warm-up and calibration steps, and a safety note: demo loads are LEDs, a low-voltage relay module or a certified smart plug; never hand-wired mains.
- hardware/docs/ONBOARDING.md: the exact runbook for the day a board arrives: (1) flash env, (2) provision credentials, (3) run bench_test.py, (4) pass tests/conformance, (5) flip that device's source to real, (6) confirm the badge changes. Include a troubleshooting table (no WiFi, MQTT auth fail, wrong time, noisy sensor, relay inverted).
- hardware/tools/bench_test.py: per-node checklist (state received, cmd/ack round trip, LWT on power-off) runnable against fake_node today and a real board later.
- List the tools I would need to buy and nothing else: boards, sensors, USB cable, breadboard and jumpers, optional multimeter.
Acceptance: firmware compiles for every env; bench_test passes against fake_node.

BATCH 10: EVALUATION, OBSERVABILITY, DEMO
- ai/evaluation/run_all.py runs every surviving module, fills evaluation_reports; the UI shows baseline vs method with real numbers and a "simulated" tag.
- Structured logs with correlation ids from sensor message to actuation; /metrics (Prometheus format); audit log of every actuation (who, what, why); real login with viewer/operator/admin roles; CORS restricted by config; .gitignore for db and .env; LICENSE note; CI running lint, pytest, conformance, firmware compile.
- Demo control bar: power spike, gas leak, flood, window open with AC on, night intruder, device offline, away mode. Demo script of 2 minutes, a 30-second explanation per surviving algorithm, judge Q&A, and one slide titled "What is simulated vs measured".
Acceptance: CI green; one command starts everything; README covers simulated, fake-node and real-hardware modes.

==================================================
5. REPORTING FORMAT AFTER EVERY BATCH
==================================================
1. Files added and changed.
2. Test results (real output summaries).
3. Measured numbers, baseline vs method, with the data source named.
4. Algorithms kept or deleted this batch and why (also appended to DECISIONS.md).
5. Known limitations and anything partial.
6. Anything I must do by hand (expected to be nothing until Batch 9 hardware purchases).
Then stop and wait for approval.

   
