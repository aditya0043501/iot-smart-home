# Decisions Log

Newest at the bottom. Each entry: context, decision, evidence, status.

---

## D-001 · Base the work on AETHER, not the described "Sentient Home" (Batch 0)

**Context.** The brief's "Existing State" describes WebSocket, an event bus, an MQTT layer, 501 endpoints with a DecisionArtifact contract, and SQLAlchemy. None of these is in the repo. See `CURRENT_STATE.md` §1.
**Decision.** The architect chose to treat this repo as the truth. Later batches build the missing foundation rather than assuming it.
**Consequence.** Batch 1 must also create the WebSocket and the event bus. The DecisionArtifact contract has to be *defined*, since there is nothing to preserve. Pending architect input in Batch 1.
**Status.** Accepted (architect, 2026-10-25).

## D-002 · Window state: device is the source of truth, room flag is derived (Batch 0)

**Context.** There was no window device. "WindowOpen" was a free-text fact typed into the expert-system API, so window-open-with-AC-on could never fire from real state.
**Decision.**
- Add `dev-9` (`device_type="window"`, field `is_open`).
- `DeviceStateStore.room_flags()` computes `window_open` and `hvac_active` on every read. Nothing stores a room flag.
- SG-04 fires when both flags are true in the **same room**.
- "HVAC active" means thermostat `state=1`, `mode != off`, and `power_watts ≥ 50 W`. The power gate excludes standby and fan-only.

**Evidence.** `tests/test_window_guard.py`: 7 tests, including end-to-end through the simulator at 08:00.
**Status.** Done.

## D-003 · Code the brief excludes from the product: remove or move? (Batch 0, OPEN)

**Context.** BFS/DFS/UCS/Greedy comparisons, vacuum coverage, HC/SA/GA, MDP and full STRIPS exist, pass their tests, and each has an AI Lab card in the UI. The brief says they are not in the product.
**Proposal.** Move them to `docs/teaching_notebooks/` in the batch that ships each replacement: B5 (MDP, HC/SA/GA), B6 (search comparison, vacuum), B7 (STRIPS). Remove their API routes and AI Lab cards at the same time, so the UI is never left with dead cards. Nothing is deleted in Batch 0.
**Status.** Needs architect approval.

## D-004 · Injectable Clock and drift-free sim speed (Batch 0)

**Context.** Time was read from `datetime.now()`, `datetime.utcnow()` (a UTC vs local bug in night-motion injection) and `time.time()`. There was no speed factor. A per-tick accumulator (`t += speed × interval`) drifts by `speed × jitter` every tick.
**Decision.** `core/clock.py` gets a `Clock` protocol with `SystemClock`, `FakeClock` (tests) and `SimClock`. `SimClock` computes time from a single anchor, so the error does not accumulate. Speed is clamped to `[0, SIM_MAX_SPEED]` (default 600). `reset()` restarts a scenario at a fixed time. The simulator's RNG can be seeded (`SIM_SEED`).
**Evidence (simulated).** `test_sim_clock_has_no_drift_at_600x_over_many_uneven_ticks`: 12 000 ticks at 600× with ±17 ms jitter. SimClock error < 1 ms; the naive accumulator was off by more than 60 s.
**Status.** Done.

## D-005 · Placeholder outputs that look like real AI results (Batch 0, flagged)

**Context.** `/api/simulate/spike` and `/intrusion` write fixed scores (0.93, 0.88) labelled IsolationForest and ZScore. `/api/ai/status` lists models that do not exist (XGBoost, K-Means, Q-Learning). This breaks P5.
**Decision.** Leave them unchanged in Batch 0 so the UI keeps working. Replace them with real detector output in B4 and honest status in B10. Until then, `CURRENT_STATE.md` §3 documents them as placeholders.
**Status.** Open, scheduled.

## D-006 · New dev dependency: pytest (Batch 0)

pytest is added only in `requirements-dev.txt` (pinned 8.3.3), because the acceptance criterion requires it. It is not a runtime dependency. Separately, `python-dotenv` is now optional in `config.py`: if it is missing, the app reads real environment variables only.
