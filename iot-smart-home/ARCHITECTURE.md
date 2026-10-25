# Architecture (real status, Batch 0)

Legend: **[built]** exists and is tested · **[partial]** exists, incomplete · **[planned Bn]** does not exist yet; batch that adds it.

```
┌──────────────────────────────────────────────────────────────────────┐
│ UI  index.html + js/*.js  (6 views, plain scripts, CDN libs)  [built]│
│     polls REST every 20 s via js/ai-bridge.js                        │
├──────────────────────────────────────────────────────────────────────┤
│ API  FastAPI main.py (routes.py, classical_routes.py)       [partial]│
│      stdlib fallback server.py (classical endpoints only)     [built]│
│      WebSocket                                            [planned B1]│
├──────────────────────────────────────────────────────────────────────┤
│ Application services                                                 │
│   simulator loop (main.py)                                  [partial]│
│   command pipeline / rule engine / scene executor      [planned B3,B7]│
│   AI services (ML, LLM)                                 [planned B4,B8]│
├──────────────────────────────────────────────────────────────────────┤
│ Domain core  ai-service/core/                                        │
│   DeviceStateStore  (device state = single source of truth)   [built]│
│   room flags        (derived on read, never stored)           [built]│
│   SafetyGuard       (SG-04 live; SG-01..03, 05 in B3)       [partial]│
│   room graph        classical/graph/house_graph.py            [built]│
│   event bus                                               [planned B1]│
├──────────────────────────────────────────────────────────────────────┤
│ Ports                                                                │
│   Clock  (core/clock.py: System / Fake / Sim)                 [built]│
│   DeviceTransport                                         [planned B1]│
│   TelemetryStore  (today: raw sqlite3 in database.py)     [planned B2]│
│   LLMProvider                                             [planned B8]│
├──────────────────────────────────────────────────────────────────────┤
│ Adapters                                                             │
│   SimTransport (today: simulator/data_generator.py)         [partial]│
│   MqttTransport, FakeNode, Mosquitto config               [planned B1]│
│   ESP32 firmware                                          [planned B9]│
└──────────────────────────────────────────────────────────────────────┘
```

## Data flow today

```
simulator.generate_snapshot(clock=runtime.clock)
   │  (or POST /api/readings from the frontend, is_simulated=0)
   ▼
database.insert_reading()  ──►  sensor_readings
   │
   ▼
core.runtime.ingest(rows)
   ├─ DeviceStateStore.apply_many()       latest state per device
   ├─ SafetyGuard.evaluate()              reads derived room_flags()
   └─ new alert ─► database.insert_anomaly()  ──► anomaly_events ──► UI alert panel
```

## Key rules

1. **Device state is the truth.** `room_flags(room)` computes `window_open` and `hvac_active` from device readings every time it is called. Nothing stores a room flag.
2. **Time comes from a Clock.** The simulator and the guard take a `Clock`. Tests use `FakeClock`. The running service uses `SimClock(speed=SIM_SPEED)`, clamped to `SIM_MAX_SPEED`. `SimClock` is anchored to one start point, so it does not drift.
3. **Reproducible scenarios.** `generate_snapshot(clock, rng)` with the same clock time and RNG seed gives identical output. `SIM_SEED` sets this for a whole run.

## Known gaps carried forward

- `sensor_readings.ts` is written by SQLite as wall-clock time, not sim time. At `SIM_SPEED > 1`, time-window queries such as `/api/readings?hours=` therefore use real time. This gets fixed with the telemetry store in Batch 2.
- The device list is duplicated in `js/store.js` and `simulator/data_generator.py`. The new `dev-9` window sensor exists on the backend only, and the UI does not list it yet.
- Guard state lives in process memory, so active alerts are lost on restart and re-raised on the next tick. Persisted alerts in `anomaly_events` survive.
