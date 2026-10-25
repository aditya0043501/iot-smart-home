"""
AETHER AI Service — Configuration
Loads .env from the project root and exposes typed settings.
"""
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv not installed: rely on real env vars only
    def load_dotenv(*_args, **_kwargs):
        return False

# Load .env from project root (one level up from ai-service/)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Fall back to .env.example defaults (no key required)
    load_dotenv(Path(__file__).parent.parent / ".env.example")


class Config:
    # Service
    AI_SERVICE_PORT: int   = int(os.getenv("AI_SERVICE_PORT", 8089))
    AI_SERVICE_HOST: str   = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
    FRONTEND_ORIGIN: str   = os.getenv("FRONTEND_ORIGIN", "http://localhost:8088")

    # LLM
    OPENAI_API_KEY: str    = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str      = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    LLM_AVAILABLE: bool    = bool(os.getenv("OPENAI_API_KEY", "").strip())

    # Feature flags
    ENABLE_ANOMALY: bool         = os.getenv("ENABLE_ANOMALY_DETECTION",    "true").lower() == "true"
    ENABLE_FORECAST: bool        = os.getenv("ENABLE_ENERGY_FORECAST",       "true").lower() == "true"
    ENABLE_OCCUPANCY: bool       = os.getenv("ENABLE_OCCUPANCY_MODEL",       "true").lower() == "true"
    ENABLE_THERMOSTAT_RL: bool   = os.getenv("ENABLE_THERMOSTAT_RL",         "true").lower() == "true"
    ENABLE_LLM_CONTROL: bool     = os.getenv("ENABLE_LLM_CONTROL",           "true").lower() == "true"
    ENABLE_LLM_INSIGHTS: bool    = os.getenv("ENABLE_LLM_INSIGHTS",          "true").lower() == "true"
    ENABLE_AUTO_GEN: bool        = os.getenv("ENABLE_AUTOMATION_GENERATOR",  "true").lower() == "true"

    # Simulator
    SIMULATOR_INTERVAL: int      = int(os.getenv("SIMULATOR_INTERVAL_SECONDS", 5))
    ANOMALY_PROBABILITY: float   = float(os.getenv("SIMULATOR_ANOMALY_PROBABILITY", 0.03))
    # Simulated-time speed factor (1 = real time). Clamped to SIM_MAX_SPEED.
    SIM_SPEED: float             = float(os.getenv("SIM_SPEED", 1))
    SIM_MAX_SPEED: float         = float(os.getenv("SIM_MAX_SPEED", 600))
    # Seed for the simulator RNG. Empty = non-deterministic (live demo).
    SIM_SEED: str                = os.getenv("SIM_SEED", "")

    # Database
    DB_PATH: str = os.getenv("DB_PATH", "ai-service/artifacts/aether.db")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
