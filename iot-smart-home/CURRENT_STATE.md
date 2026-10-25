# Current State (after Batch 0)

This file records what is actually in the repo. It was written by reading the code and running the tests, not by copying the brief.

## 1. The brief vs. the repo

The brief (`docs/BRIEF.md`) describes an "existing" Sentient Home system. This repo is **AETHER**, and much of what the brief lists does not exist yet. The architect chose to treat AETHER as the base (decision D-001).

| Brief says exists | Reality in this repo |
|---|---|
| FastAPI backend | Yes, `ai-service/main.py` + `api/routes.py`, `api/classical_routes.py`. If FastAPI is missing, it falls back to the stdlib server `ai-service/server.py` (classical endpoints only). |
| SQLAlchemy + SQLite | SQLite only, raw `sqlite3` (`ai-service/database.py`). No SQLAlchemy. |
| WebSocket live state | **Missing.** The frontend polls REST (`js/ai-bridge.js`, every 20 s for anomalies). |
| Event bus | **Missing.** |
| Device registry | Partial. A hard-coded `DEVICES` list in `simulator/data_generator.py`, mirrored by hand in `js/store.js`. |
| Safety guard SG-xx | **Added in Batch 0:** `core/guard.py`, SG-04 only. |
| Simulator with scenario injection | Partial. A random snapshot generator plus three demo endpoints (`/api/simulate/spike`, `/intrusion`, `/away`). No physics model, no scenario script. |
| 30 days seeded history | **Missing.** The DB fills only while the service runs (one snapshot every 5 s). |
| MQTT transport, adapter registry, HA discovery, `/hardware/test` | **Missing.** There is no hardware layer of any kind. |
| Frontend: 9 views, ES modules, API client, WS hook | 6 views (landing, AI lab, dashboard, devices, automation, settings). Plain `<script>` files, not ES modules. Tailwind/Lucide/Chart.js/Three.js from CDNs. No WS hook. |
| `ai/ml`, `ai/classical`, `ai/evaluation` returning 501 + DecisionArtifact | **No 501 endpoints and no DecisionArtifact contract.** `ai-service/classical/` holds 9 working algorithms. `models/`, `llm/`, `pipelines/` are empty packages. |
| Known bug: window_open_ac_on flag mismatch | No window device and no room flag existed. WindowOpen/ACOn were only free-text facts typed into the expert-system endpoint, so the alert could never fire from real device state. **Fixed in Batch 0.** |
| Sim clock drift at 600x | There was no speed factor. Time came from `datetime.now()`, `datetime.utcnow()` (UTC/local mix-up) and `time.time()`. **Fixed in Batch 0** with an injectable `Clock`. |
| ARCHITECTURE.md, ALGORITHM_MAP.md stale | Did not exist. **Created in Batch 0.** |
| Python 3.12 | README says 3.9+. Batch 0 was verified on **Python 3.10.12** (sandbox). Not yet run on 3.12. |

## 2. What runs

| Component | How to start | Status |
|---|---|---|
| Frontend | `python3 serve.py` → http://localhost:8088 | Runs. Device state is mock data in `js/store.js`. |
| Classical AI server (stdlib) | `python3 ai-service/server.py` → :8089 | Runs with no pip installs. Verified in Batch 0: `/health` and `/api/classical/expert/forward` respond. |
| FastAPI service + simulator loop + guard | `pip install -r requirements.txt` then `python3 ai-service/main.py` | Code compiles. **Not run in Batch 0**: the sandbox has no network, so FastAPI could not be installed. |
| Tests | `pip install -r requirements-dev.txt` then `pytest` | See §4. |

## 3. Endpoints that return placeholders (instead of 501)

| Endpoint | What it really returns |
|---|---|
| `GET /api/forecast/energy` | A hand-written heuristic (`0.3 + activity*2.2 + …`), labelled `heuristic_baseline`. No model. |
| `GET /api/ai/status` | Says IsolationForest, XGBoost, K-Means and Q-Learning exist. None of them exist. |
| `POST /api/simulate/spike` | Writes a hard-coded anomaly row with a fixed score of 0.93 and a canned explanation. No detector runs. |
| `POST /api/simulate/intrusion` | Same pattern, fixed score 0.88, labelled "ZScore". |
| `GET /api/models/status` | An empty table; nothing ever trains. |

These break principle P5 (no invented metrics). They are flagged for Batch 4 / Batch 10 (D-005).

## 4. Test coverage

There are 45 test functions, all passing:

- 19 are new in Batch 0 (`tests/`).
- 26 already existed (`ai-service/evaluation/`), and pytest now collects them too.

The slowest test takes 42.6 ms, and none sleeps. The existing evaluation tests check the classical algorithms only. Nothing tests the REST routes, the DB layer (apart from the new migration test) or the frontend.

pytest itself could not be installed in the sandbox, which has no network. The same test functions were run with a small stdlib runner that calls every `test_*` function. Run `pytest` once locally to confirm.

## 5. Changes in Batch 0

- `ai-service/core/` (new): the `Clock` port (System/Fake/Sim), `DeviceStateStore` with derived room flags, `SafetyGuard` (SG-04), and runtime wiring.
- Simulator: injectable clock and RNG, new device `dev-9` (window contact), and the UTC/local hour bug fixed.
- DB: `is_open` column, plus an automatic migration for existing `aether.db` files.
- `GET /api/guard/status` (new). Guard alerts are written to `anomaly_events`, so the existing UI alert panel shows them.
- The brief had been pasted into the bottom of README.md. It was moved to `docs/BRIEF.md`.
