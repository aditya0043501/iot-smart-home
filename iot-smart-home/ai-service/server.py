"""
AETHER Classical & ML AI Service — Zero-Dependency Standalone HTTP Server
-------------------------------------------------------------------------
Uses Python standard library (http.server, json, urllib) so it runs
immediately with `python3 ai-service/server.py` without requiring pip install!
Also compatible with FastAPI when dependencies are installed.
"""

import sys
import json
import logging
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ensure ai-service root is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from classical.graph.house_graph import house_graph
from classical.logic.wumpus import (
    simulate_hazard_scenario,
    diagnose_smart_home_sensors,
    HAZARDS
)
from classical.planning.strips import (
    STRIPSPlanner,
    PRESET_GOALS,
    get_default_initial_state
)
from classical.search.routing import SearchComparisonEngine
from classical.csp.scheduler import ApplianceCSPSolver, get_default_appliances
from classical.logic.expert_system import ExpertSystem, get_default_smart_home_rules
from classical.probabilistic.bayes_net import SmartHomeBayesNet
from classical.probabilistic.mdp_thermostat import ThermostatMDP
from classical.fuzzy.climate_fuzzy import ClimateFuzzyController
from classical.optimization.energy_opt import (
    OptimizerEngine,
    HOURLY_TARIFF,
    APPLIANCES_TO_OPTIMIZE
)

planner = STRIPSPlanner()
search_engine = SearchComparisonEngine()
expert_system = ExpertSystem()
bayes_net = SmartHomeBayesNet()
thermostat_mdp = ThermostatMDP()
fuzzy_controller = ClimateFuzzyController()
optimizer_engine = OptimizerEngine()

PORT = 8089
HOST = "0.0.0.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("aether-ai-server")


class AetherRequestHandler(BaseHTTPRequestHandler):
    """Handles REST API requests with full CORS support."""

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    # ── GET Routes ───────────────────────────────────────────────
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ("", "/health"):
            self._send_json(200, {
                "status": "ok",
                "service": "AETHER AI Service (Standard Engine)",
                "port": PORT,
                "algorithms_active": ["house_graph", "wumpus_hazard_inference"]
            })

        elif path == "/api/classical/graph":
            self._send_json(200, house_graph.to_dict())

        elif path == "/api/classical/hazards":
            self._send_json(200, {"hazards": HAZARDS})

        elif path == "/api/classical/csp/appliances":
            apps = get_default_appliances()
            self._send_json(200, {
                "appliances": [a.to_dict() for a in apps.values()],
                "default_power_cap_watts": 3800.0,
                "default_horizon_slots": 12
            })

        elif path == "/api/classical/expert/rules":
            rules = get_default_smart_home_rules()
            self._send_json(200, {"rules": [r.to_dict() for r in rules]})

        elif path == "/api/classical/bayes/structure":
            self._send_json(200, {
                "nodes": [
                    {
                        "name": n.name,
                        "description": n.description,
                        "parents": n.parents,
                        "possible_values": n.values
                    }
                    for n in bayes_net.nodes.values()
                ]
            })

        elif path == "/api/classical/optimization/tariffs":
            self._send_json(200, {
                "hourly_tariffs_inr": HOURLY_TARIFF,
                "appliances": APPLIANCES_TO_OPTIMIZE
            })

        elif path == "/api/classical/planning/presets":
            self._send_json(200, {
                "presets": {
                    k: {
                        "title": v["title"],
                        "description": v["description"],
                        "goal_predicates": sorted(list(v["goal_predicates"]))
                    }
                    for k, v in PRESET_GOALS.items()
                },
                "default_state": sorted(list(get_default_initial_state()))
            })

        elif path == "/api/ai/status":
            self._send_json(200, {
                "models_ready": True,
                "classical_ai": {
                    "wumpus_agent": {"status": "active", "type": "Propositional Model Checking (TT-Entails)"},
                    "house_graph": {"status": "active", "rooms": len(house_graph.nodes)}
                }
            })

        else:
            self._send_json(404, {"error": f"Endpoint not found: {path}"})

    # ── POST Routes ──────────────────────────────────────────────
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            body = self._read_json_body()
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON body: {str(e)}"})
            return

        if path == "/api/classical/wumpus/simulate":
            loc = body.get("hazard_location", "R3")
            htype = body.get("hazard_type", "FIRE")
            static_sensors = body.get("static_sensor_rooms", ["R6", "R5"])

            if loc not in house_graph.nodes:
                self._send_json(400, {"error": f"Invalid room: {loc}"})
                return
            if htype not in HAZARDS:
                self._send_json(400, {"error": f"Invalid hazard: {htype}. Allowed: {HAZARDS}"})
                return

            trace = simulate_hazard_scenario(
                hazard_location=loc,
                hazard_type=htype,
                static_sensor_rooms=static_sensors
            )
            self._send_json(200, {
                "status": "success",
                "hazard_location": loc,
                "hazard_type": htype,
                "total_steps": len(trace),
                "trace": trace,
                "final_confirmed_hazards": trace[-1]["confirmed_hazards"] if trace else {}
            })

        elif path == "/api/classical/wumpus/diagnose":
            readings = body.get("sensor_readings", {})
            result = diagnose_smart_home_sensors(readings)
            self._send_json(200, result)

        elif path == "/api/classical/planning/solve":
            goal_key = body.get("goal_key", "movie_night")
            custom_goals = body.get("custom_goals")
            if custom_goals:
                goals = set(custom_goals)
            elif goal_key in PRESET_GOALS:
                goals = PRESET_GOALS[goal_key]["goal_predicates"]
            else:
                self._send_json(400, {"error": f"Unknown goal: {goal_key}"})
                return

            s0_raw = body.get("initial_state")
            s0 = set(s0_raw) if s0_raw else get_default_initial_state()
            plan_res = planner.solve(s0, goals)
            self._send_json(200, plan_res)

        elif path == "/api/classical/planning/replan":
            goal_key = body.get("goal_key", "movie_night")
            failed_dev = body.get("failed_device_id", "dev-1")
            if goal_key not in PRESET_GOALS:
                self._send_json(400, {"error": f"Unknown goal: {goal_key}"})
                return

            goals = PRESET_GOALS[goal_key]["goal_predicates"]
            s0 = get_default_initial_state()
            replan_res = planner.replan_on_failure(s0, goals, failed_device_id=failed_dev)
            self._send_json(200, replan_res)

        elif path == "/api/classical/search/compare":
            start_room = body.get("start_room", "R7")
            goals = body.get("goals")
            blocked = body.get("blocked_rooms")
            heuristic = body.get("heuristic", "euclidean")

            if start_room not in house_graph.nodes:
                self._send_json(400, {"error": f"Invalid start room: {start_room}"})
                return

            res = search_engine.compare_all(
                start=start_room,
                goals=goals,
                blocked_rooms=blocked,
                heuristic_type=heuristic
            )
            self._send_json(200, res)

        elif path == "/api/classical/search/vacuum":
            start_room = body.get("start_room", "R1")
            if start_room not in house_graph.nodes:
                self._send_json(400, {"error": f"Invalid start room: {start_room}"})
                return
            res = search_engine.compute_vacuum_coverage(start=start_room)
            self._send_json(200, res)

        elif path == "/api/classical/csp/solve":
            p_cap = float(body.get("power_cap_watts", 3500.0))
            horizon = int(body.get("horizon_slots", 12))
            use_ac3 = bool(body.get("use_ac3", True))
            solver = ApplianceCSPSolver(power_cap_watts=p_cap, total_horizon_slots=horizon)
            res = solver.solve(use_ac3=use_ac3)
            self._send_json(200, res)

        elif path == "/api/classical/expert/forward":
            facts = body.get("facts", ["WindowOpen", "ACOn"])
            res = expert_system.forward_chain(set(facts))
            self._send_json(200, res)

        elif path == "/api/classical/expert/backward":
            goal = body.get("goal", "StrobeSirenActive")
            facts = body.get("known_facts", ["MotionDetectedYard", "PerimeterArmed", "NoResidentPresent"])
            res = expert_system.backward_chain(goal, set(facts))
            self._send_json(200, res)

        elif path == "/api/classical/bayes/query":
            evidence = body.get("evidence", {})
            res = bayes_net.evaluate_live_beliefs(evidence)
            self._send_json(200, res)

        elif path == "/api/classical/mdp/solve":
            gamma = float(body.get("gamma", 0.92))
            eps = float(body.get("epsilon", 0.001))
            bias = body.get("outdoor_bias", "Hot")
            mdp = ThermostatMDP(gamma=gamma, epsilon=eps, ambient_outdoor_bias=bias)
            res = mdp.value_iteration()
            self._send_json(200, res)

        elif path == "/api/classical/fuzzy/compute":
            t = float(body.get("temperature", 26.5))
            h = float(body.get("humidity", 65.0))
            occ = float(body.get("occupancy", 0.8))
            res = fuzzy_controller.compute(t, h, occ)
            self._send_json(200, res)

        elif path == "/api/classical/optimization/compare":
            seed = body.get("seed_schedule")
            res = optimizer_engine.compare_all(seed_schedule=seed)
            self._send_json(200, res)

        else:
            self._send_json(404, {"error": f"Endpoint not found: {path}"})

    def log_message(self, format, *args):
        # Clean logging
        log.info("%s - %s", self.address_string(), format % args)


def run_server():
    server = ThreadingHTTPServer((HOST, PORT), AetherRequestHandler)
    log.info(f"🚀 AETHER Classical AI Server listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Server shutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
