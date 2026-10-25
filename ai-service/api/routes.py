"""
AETHER AI Service — FastAPI REST endpoints
------------------------------------------
All endpoints the existing frontend (port 8088) or the AI pipeline
calls. Every route returns JSON. CORS is configured in main.py.

Endpoint map:
  GET  /health                   — liveness check
  GET  /api/readings             — recent sensor readings (filtered)
  GET  /api/readings/summary     — per-device latest + rolling stats
  POST /api/readings             — frontend pushes real device state
  GET  /api/anomalies            — recent anomaly events
  POST /api/simulate/spike       — demo: inject a power spike
  POST /api/simulate/intrusion   — demo: inject a night intrusion
  POST /api/simulate/away        — demo: switch all devices to away mode
  GET  /api/models/status        — which models are trained + their metrics
  GET  /api/forecast/energy      — energy forecast (next 12 h)
  GET  /api/ai/status            — summary of all AI feature states
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import database as db
from config import config

# Models are imported lazily so the service starts even when
# models haven't been trained yet.

router = APIRouter()

# ── Health ────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {
        "status": "ok",
        "ts": datetime.utcnow().isoformat() + "Z",
        "reading_count": db.get_reading_count(),
        "features": {
            "anomaly":    config.ENABLE_ANOMALY,
            "forecast":   config.ENABLE_FORECAST,
            "occupancy":  config.ENABLE_OCCUPANCY,
            "thermostat": config.ENABLE_THERMOSTAT_RL,
            "llm":        config.LLM_AVAILABLE and config.ENABLE_LLM_CONTROL,
        },
    }


# ── Sensor Readings ───────────────────────────────────────────

@router.get("/api/readings")
def get_readings(
    device_id: str | None = Query(None, description="Filter by device ID"),
    hours:     float      = Query(24,   description="Lookback window in hours"),
    limit:     int        = Query(500,  description="Max rows returned"),
):
    rows = db.fetch_readings(device_id=device_id, limit=limit, hours=hours)
    return {"count": len(rows), "readings": rows}


@router.get("/api/readings/summary")
def readings_summary():
    """Latest reading + 1-hour rolling stats per device."""
    rows = db.fetch_readings(hours=1, limit=2000)
    if not rows:
        return {"devices": {}}

    from collections import defaultdict
    by_dev: dict[str, list] = defaultdict(list)
    for r in rows:
        by_dev[r["device_id"]].append(r)

    summary = {}
    for dev_id, readings in by_dev.items():
        latest = readings[0]  # newest first
        powers = [r["power_watts"] for r in readings if r["power_watts"] is not None]
        summary[dev_id] = {
            "latest": latest,
            "avg_power_1h": round(sum(powers) / len(powers), 2) if powers else 0,
            "max_power_1h": round(max(powers), 2) if powers else 0,
            "reading_count_1h": len(readings),
        }
    return {"devices": summary}


class DeviceStatePayload(BaseModel):
    device_id:   str
    device_name: str
    device_type: str
    room:        str
    state:       int
    power_watts: float = 0.0
    brightness:  float | None = None
    temperature: float | None = None
    target_temp: float | None = None
    humidity:    float | None = None
    battery_pct: float | None = None
    is_locked:   int   | None = None
    fan_speed_num: float | None = None
    is_recording: int  | None = None
    motion_detected: int | None = None


@router.post("/api/readings", status_code=201)
def post_reading(payload: DeviceStatePayload):
    """Frontend pushes real device state here so models train on it."""
    row = payload.model_dump()
    row["is_simulated"] = 0  # real data
    row["anomaly_score"] = 0.0
    db.insert_reading(row)
    return {"status": "recorded", "device_id": payload.device_id}


# ── Anomaly Events ─────────────────────────────────────────────

@router.get("/api/anomalies")
def get_anomalies(limit: int = Query(20)):
    return {"anomalies": db.fetch_anomalies(limit=limit)}


# ── Demo Triggers (Phase 5 "fire the pipeline" buttons) ────────

@router.post("/api/simulate/spike")
def demo_power_spike():
    """
    Inject an extreme power reading for dev-2 (thermostat) to
    immediately trigger the anomaly detector.
    """
    row = {
        "device_id": "dev-2", "device_name": "Master Climate Thermostat",
        "device_type": "thermostat", "room": "Living Room",
        "state": 1, "power_watts": 4800.0,   # ~4× normal
        "temperature": 38.5, "target_temp": 22.0, "humidity": 68.0,
        "is_simulated": 1, "anomaly_score": 0.93,
    }
    db.insert_reading(row)
    db.insert_anomaly({
        "device_id":  "dev-2",
        "algorithm":  "IsolationForest",
        "score":      0.93,
        "threshold":  0.60,
        "feature_values": json.dumps({"power_watts": 4800, "temperature": 38.5}),
        "explanation": "Power draw is 4× above the 1-hour rolling average. "
                       "Combined with ambient temperature 14°C above target, "
                       "this indicates a possible compressor fault or refrigerant leak.",
        "suggested_action": "Check AC unit. If fault persists >5 min, schedule maintenance.",
    })
    return {"status": "spike_injected", "anomaly_score": 0.93}


@router.post("/api/simulate/intrusion")
def demo_night_intrusion():
    """
    Inject a motion-detected camera reading at odd hours.
    """
    row = {
        "device_id": "dev-7", "device_name": "Backyard Security Cam HD",
        "device_type": "camera", "room": "Living Room",
        "state": 1, "power_watts": 8.5,
        "is_recording": 1, "motion_detected": 1,
        "is_simulated": 1, "anomaly_score": 0.88,
    }
    db.insert_reading(row)
    db.insert_anomaly({
        "device_id":  "dev-7",
        "algorithm":  "ZScore",
        "score":      0.88,
        "threshold":  0.60,
        "feature_values": json.dumps({"motion_detected": 1, "hour": datetime.now().hour}),
        "explanation": "Motion detected by backyard camera at an unusual hour. "
                       "Historical data shows zero motion events at this time of day.",
        "suggested_action": "Review live feed. If confirmed intrusion, notify emergency contacts.",
    })
    return {"status": "intrusion_simulated", "anomaly_score": 0.88}


@router.post("/api/simulate/away")
def demo_away_mode():
    """
    Generate a batch of 'away mode' readings: all lights off,
    thermostat in ECO, fan off, lock locked.
    """
    away_devices = [
        {"device_id":"dev-1","device_name":"Living Room Main Lights","device_type":"light","room":"Living Room","state":0,"power_watts":0.0,"brightness":0.0},
        {"device_id":"dev-2","device_name":"Master Climate Thermostat","device_type":"thermostat","room":"Living Room","state":1,"power_watts":120.0,"temperature":32.0,"target_temp":28.0,"humidity":60.0},
        {"device_id":"dev-3","device_name":"Front Entrance Smart Lock","device_type":"lock","room":"Living Room","state":1,"is_locked":1,"battery_pct":93.5,"power_watts":0.5},
        {"device_id":"dev-4","device_name":"AeroFlow Ceiling Fan","device_type":"fan","room":"Bedroom","state":0,"power_watts":0.0,"fan_speed_num":0},
        {"device_id":"dev-5","device_name":"Bedroom Reading Lamp","device_type":"light","room":"Bedroom","state":0,"power_watts":0.0,"brightness":0.0},
        {"device_id":"dev-7","device_name":"Backyard Security Cam HD","device_type":"camera","room":"Living Room","state":1,"power_watts":8.5,"is_recording":1,"motion_detected":0},
    ]
    for r in away_devices:
        r["is_simulated"] = 1
        r["anomaly_score"] = 0.0
        db.insert_reading(r)

    return {"status": "away_mode_simulated", "devices_updated": len(away_devices)}


# ── Model Status ───────────────────────────────────────────────

@router.get("/api/models/status")
def model_status():
    with db.get_conn() as conn:
        rows = conn.execute("SELECT * FROM model_metadata").fetchall()
    return {"models": [dict(r) for r in rows]}


# ── Energy Forecast stub (filled by Phase 2 model) ─────────────

@router.get("/api/forecast/energy")
def energy_forecast():
    """
    Returns a 12-point hourly energy forecast.
    Pre-Phase-2: returns simulated values.
    Post-Phase-2: returns XGBoost / LSTM predictions.
    """
    # Check if a trained model artifact exists
    from pathlib import Path
    model_path = Path(__file__).parent.parent / "artifacts" / "energy_forecast.joblib"

    if model_path.exists():
        # Load and predict (wired in Phase 2)
        return {"source": "model", "forecast": _load_and_predict_energy()}
    else:
        # Return heuristic baseline
        from simulator.data_generator import _activity_level, _ambient_temp
        now = datetime.now()
        forecast = []
        for i in range(12):
            hour = (now.hour + i) % 24
            act  = _activity_level(hour)
            temp = _ambient_temp(hour)
            kw   = round(0.3 + act * 2.2 + (temp - 26) * 0.04, 2)
            forecast.append({
                "hour":       (now + timedelta(hours=i)).strftime("%H:00"),
                "predicted_kw": kw,
                "source":     "heuristic_baseline",
            })
        return {"source": "heuristic_baseline", "forecast": forecast}


def _load_and_predict_energy():
    """Stub called when model artifact exists (implemented in Phase 2)."""
    return []


# ── AI Status Summary ─────────────────────────────────────────

@router.get("/api/ai/status")
def ai_status():
    reading_count = db.get_reading_count()
    hours_of_data = reading_count / (8 * 12)  # 8 devices × 12 reads/min
    return {
        "reading_count": reading_count,
        "estimated_hours_of_data": round(hours_of_data, 1),
        "models_ready": reading_count >= 200,
        "features": {
            "anomaly_detection": {
                "enabled": config.ENABLE_ANOMALY,
                "algorithm": "IsolationForest + EWMA Z-score",
                "status": "training" if reading_count < 200 else "active",
            },
            "energy_forecast": {
                "enabled": config.ENABLE_FORECAST,
                "algorithm": "XGBoost (time-series features)",
                "status": "heuristic_baseline" if reading_count < 200 else "model_active",
            },
            "occupancy_model": {
                "enabled": config.ENABLE_OCCUPANCY,
                "algorithm": "K-Means clustering",
                "status": "accumulating_data",
            },
            "thermostat_rl": {
                "enabled": config.ENABLE_THERMOSTAT_RL,
                "algorithm": "Q-Learning (tabular)",
                "status": "accumulating_data",
            },
            "llm_control": {
                "enabled": config.ENABLE_LLM_CONTROL,
                "llm_available": config.LLM_AVAILABLE,
                "model": config.OPENAI_MODEL if config.LLM_AVAILABLE else "unavailable",
            },
        },
    }
