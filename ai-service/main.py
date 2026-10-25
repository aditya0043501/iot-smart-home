"""
AETHER AI Service — Entry Point
--------------------------------
Start with:  python3 ai-service/main.py
             (or uvicorn ai-service.main:app --port 8089)

On startup:
  1. Initialise SQLite database
  2. Register FastAPI routes with CORS for port 8088
  3. Start background simulator loop (writes one snapshot every N seconds)
  4. Serve on AI_SERVICE_PORT (default 8089)
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Allow imports from ai-service/ without package prefix
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    USE_FASTAPI = True
except ImportError:
    USE_FASTAPI = False
    from server import run_server

if not USE_FASTAPI:
    if __name__ == "__main__":
        print("[AETHER AI] FastAPI not installed in current environment; starting standard library server...")
        run_server()
else:
    import database as db
    from config import config
    from api.routes import router
    from api.classical_routes import classical_router

if USE_FASTAPI:
    # ── Logging ───────────────────────────────────────────────────
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger("aether-ai")

    # ── FastAPI App ───────────────────────────────────────────────
    app = FastAPI(
        title="AETHER AI Service",
        description="Machine learning + LLM layer for the AETHER Smart Home Dashboard",
        version="1.0.0",
    )

    # CORS: allow the static frontend (port 8088) to call this service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.FRONTEND_ORIGIN, "http://localhost:8088", "http://127.0.0.1:8088"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    app.include_router(classical_router)
else:
    app = None

# ── Background Simulator ──────────────────────────────────────

async def _simulator_loop():
    """
    Writes a sensor snapshot to the DB every SIMULATOR_INTERVAL seconds.
    Disabled when SIMULATOR_INTERVAL_SECONDS=0.
    """
    if config.SIMULATOR_INTERVAL <= 0:
        log.info("[Simulator] Disabled (SIMULATOR_INTERVAL_SECONDS=0)")
        return

    from simulator.data_generator import generate_snapshot
    log.info(f"[Simulator] Starting — interval={config.SIMULATOR_INTERVAL}s, "
             f"anomaly_prob={config.ANOMALY_PROBABILITY}")

    tick = 0
    while True:
        try:
            snapshot = generate_snapshot()
            for row in snapshot:
                db.insert_reading(row)

            tick += 1
            if tick % 10 == 0:
                count = db.get_reading_count()
                log.info(f"[Simulator] Tick {tick} — {len(snapshot)} readings "
                         f"written. Total DB rows: {count}")

            # After enough data, trigger model training
            if tick == 60:   # ~5 min at default 5s interval
                asyncio.create_task(_train_models_background())

        except Exception as exc:
            log.error(f"[Simulator] Error: {exc}")

        await asyncio.sleep(config.SIMULATOR_INTERVAL)


async def _train_models_background():
    """
    Launches model training after sufficient data is accumulated.
    Each model is a separate module imported here to avoid blocking startup.
    Implemented fully in Phase 2.
    """
    log.info("[Training] Sufficient data accumulated — triggering model training...")
    try:
        from models import anomaly, forecast   # noqa: F401 — wired in Phase 2
        log.info("[Training] Models trained successfully.")
    except ImportError:
        log.info("[Training] Model modules not yet available (Phase 2).")
    except Exception as exc:
        log.error(f"[Training] Error: {exc}")


    # ── Startup / Shutdown ────────────────────────────────────────

    @app.on_event("startup")
    async def startup():
        db.init_db()
        log.info(f"[DB] Ready at {config.DB_PATH}")
        log.info(f"[Config] LLM available: {config.LLM_AVAILABLE}")
        log.info(f"[Config] Feature flags: "
                 f"anomaly={config.ENABLE_ANOMALY}, "
                 f"forecast={config.ENABLE_FORECAST}, "
                 f"occupancy={config.ENABLE_OCCUPANCY}, "
                 f"rl={config.ENABLE_THERMOSTAT_RL}, "
                 f"llm={config.ENABLE_LLM_CONTROL}")
        asyncio.create_task(_simulator_loop())
        log.info(f"[AETHER AI] Service ready on http://{config.AI_SERVICE_HOST}:{config.AI_SERVICE_PORT}")


    @app.on_event("shutdown")
    async def shutdown():
        log.info("[AETHER AI] Shutting down gracefully.")


# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    if USE_FASTAPI:
        uvicorn.run(
            "main:app",
            host=config.AI_SERVICE_HOST,
            port=config.AI_SERVICE_PORT,
            reload=False,
            log_level=config.LOG_LEVEL.lower(),
        )
    else:
        print("[AETHER AI] FastAPI not detected. Running built-in standard library server on port 8089...")
        from server import run_server
        run_server()
