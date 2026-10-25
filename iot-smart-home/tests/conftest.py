"""Make ai-service/ importable (it has a hyphen, so it is not a package name)."""
import sys
from pathlib import Path

AI_SERVICE = Path(__file__).resolve().parent.parent / "ai-service"
if str(AI_SERVICE) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE))
