"""Small web server for showing the network simulation."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from benchmarking import run_benchmarks
from infection_simulation import infection_step
from infection_simulation import start_simulation
from network_graph import create_custom_network
from network_graph import create_network
from optimization_algorithms import divide_and_conquer_patch
from optimization_algorithms import dynamic_programming_patch
from optimization_algorithms import greedy_patch


ROOT = Path(__file__).parent
BUDGET = 120


def make_state():
    """Make the starting dashboard data."""
    network = create_network(15, 0.1, 42)
    simulation = start_simulation(network, 0.85, 0, 42)
    state_data = {
        "network": network,
        "simulation": simulation,
        "patched": set(),
        "mode": "random",
        "budget": BUDGET,
        "algorithm": {},
    }
    return state_data


state = make_state()


def reset_state():
    """Reset progress while keeping a custom network or falling back to random."""
    global state
    if state.get("mode") == "custom" and "custom_config" in state:
        config = state["custom_config"]
        state = make_custom_state(config["nodes"], config["edges"], config["budget"])
        state["custom_config"] = config
    else:
        state = make_state()


def make_custom_state(node_values, edge_values, budget):
    """Make a dashboard state from values entered by the user and store config for reset."""
    network = create_custom_network(node_values, edge_values)
    simulation = start_simulation(network, 0.85, 0, 42)
    return {
        "network": network,
        "simulation": simulation,
        "patched": set(),
        "mode": "custom",
        "budget": budget,
        "algorithm": {},
        "custom_config": {
            "nodes": node_values,
            "edges": edge_values,
            "budget": budget,
        },
    }


def configure_custom_network(data):
    """Check custom values and replace the current network."""
    node_count = int(data.get("node_count", 0))
    edge_count = int(data.get("edge_count", 0))
    budget = int(data.get("budget", BUDGET))
    node_values = data.get("nodes", [])
    edge_values = data.get("edges", [])

    if node_count < 1:
        raise ValueError("number of nodes must be at least 1")
    if edge_count < 0:
        raise ValueError("number of edges cannot be negative")
    if budget < 0:
        raise ValueError("budget must be non-negative")
    if len(node_values) != node_count:
        raise ValueError("node data does not match the node count")
    if len(edge_values) > edge_count:
        raise ValueError("too many edges were supplied")

    for node in node_values:
        vulnerability = int(node["vulnerability"])
        cost = int(node["cost"])
        if vulnerability < 1 or vulnerability > 10:
            raise ValueError("vulnerability must be from 1 to 10")
        if cost < 1:
            raise ValueError("patch cost must be positive")

    new_state = make_custom_state(node_values, edge_values, budget)
    global state
    state = new_state


def make_algorithm_steps(algorithm_name):
    """Make simple text steps for the selected algorithm."""
    if algorithm_name == "dc":
        algorithm = divide_and_conquer_patch
        title = "Divide and Conquer"
    elif algorithm_name == "greedy":
        algorithm = greedy_patch
        title = "Greedy Algorithm"
    elif algorithm_name == "dp":
        algorithm = dynamic_programming_patch
        title = "Dynamic Programming"
    else:
        raise ValueError("unknown algorithm")

    network = state["network"]
    budget = state["budget"]
    selected = algorithm(network, budget)
    total_risk = 0
    for node in network["nodes"]:
        if node["id"] in selected:
            total_risk += node["vulnerability"] * node["degree"]

    start_explanations = {
        "dc": "The {}-node network is split recursively into smaller groups. "
        "Groups of four or fewer are solved directly, then their results "
        "are combined.".format(len(network["nodes"])),
        "greedy": "The {}-node network is ordered by risk reduction per cost. "
        "The algorithm keeps the highest-priority nodes that fit within "
        "the budget.".format(len(network["nodes"])),
        "dp": "A table evaluates {} nodes across every budget from 0 to {}. "
        "Each cell stores the highest risk reduction found so far.".format(
            len(network["nodes"]), budget
        ),
    }
    steps = []
    steps.append(
        {
            "text": "Starting {} with a budget of {}.".format(
                title, budget
            ),
            "explanation": start_explanations[algorithm_name],
            "node_id": None,
            "selected": [],
            "remaining_budget": budget,
        }
    )

    selected_so_far = []
    spent = 0
    for node_index, node in enumerate(network["nodes"]):
        node_id = node["id"]
        budget_before = budget - spent
        if node_id in selected:
            selected_so_far.append(node_id)
            spent += node["cost"]
            text = "Node {} was selected. Its patch cost is {}.".format(
                node_id, node["cost"]
            )
        else:
            text = "Node {} was checked and was not selected.".format(node_id)

        node_risk = node["vulnerability"] * node["degree"]
        if node["cost"] == 0:
            node_ratio = "infinite" if node_risk > 0 else "0"
        else:
            node_ratio = "{:.2f}".format(node_risk / node["cost"])

        if algorithm_name == "dc":
            group_start = 0
            group_end = len(network["nodes"])
            while group_end - group_start > 4:
                middle = (group_start + group_end) // 2
                if node_index < middle:
                    group_end = middle
                else:
                    group_start = middle
            explanation = (
                "Node {} is in the divided group covering nodes {}-{}. "
                "Its risk reduction is {} (vulnerability {} x degree {}), "
                "and its patch cost is {}. It {} the small-group result."
            ).format(
                node_id,
                network["nodes"][group_start]["id"],
                network["nodes"][group_end - 1]["id"],
                node_risk,
                node["vulnerability"],
                node["degree"],
                node["cost"],
                "is selected in" if node_id in selected else "is not selected in",
            )
        elif algorithm_name == "greedy":
            explanation = (
                "Node {} has risk reduction {}, cost {}, and priority ratio "
                "{}. The greedy result {} this node under the remaining "
                "budget of {}."
            ).format(
                node_id,
                node_risk,
                node["cost"],
                node_ratio,
                "includes" if node_id in selected else "does not include",
                budget_before,
            )
        else:
            explanation = (
                "For node {}, the DP comparison uses cost {} and risk "
                "reduction {} (vulnerability {} x degree {}). The final "
                "optimal combination {} this node."
            ).format(
                node_id,
                node["cost"],
                node_risk,
                node["vulnerability"],
                node["degree"],
                "includes" if node_id in selected else "does not include",
            )

        steps.append(
            {
                "text": text,
                "explanation": explanation,
                "node_id": node_id,
                "selected": selected_so_far[:],
                "remaining_budget": budget - spent,
            }
        )

    total_cost = 0
    for node_id in selected:
        for node in network["nodes"]:
            if node["id"] == node_id:
                total_cost += node["cost"]
                break

    steps.append(
        {
            "text": "Finished. The selected nodes are ready to be patched.",
            "explanation":             "The {} method selected nodes {} with total "
            "risk reduction {} and used {} of the {} budget.".format(
                title,
                ", ".join(str(node_id) for node_id in selected) or "none",
                total_risk,
                total_cost,
                budget,
            ),
            "node_id": None,
            "selected": selected[:],
            "remaining_budget": budget - total_cost,
        }
    )
    return title, steps, selected


def start_algorithm(algorithm_name):
    """Start a step-by-step algorithm page."""
    title, steps, selected = make_algorithm_steps(algorithm_name)
    state["algorithm"] = {
        "name": algorithm_name,
        "title": title,
        "steps": steps,
        "current": 0,
        "selected": selected,
        "simulation_history": [save_simulation_state(state["simulation"])],
    }
    return get_algorithm_data()


def save_simulation_state(simulation):
    """Save the mutable parts of a simulation so a step can be revisited."""
    return {
        "infected": set(simulation["infected"]),
        "time": simulation["time"],
        "infection_curve": simulation["infection_curve"][:],
        "random_state": simulation["random"].getstate(),
    }


def restore_simulation_state(simulation, saved_state):
    """Restore a simulation to a previously saved step."""
    simulation["infected"] = set(saved_state["infected"])
    simulation["time"] = saved_state["time"]
    simulation["infection_curve"] = saved_state["infection_curve"][:]
    simulation["random"].setstate(saved_state["random_state"])


def next_algorithm_step():
    """Move the current algorithm page forward by one step and advance infection simulation."""
    algorithm_data = state["algorithm"]
    if not algorithm_data:
        raise ValueError("an algorithm has not been started")

    if algorithm_data["current"] >= len(algorithm_data["steps"]) - 1:
        return get_algorithm_data()

    algorithm_data["current"] += 1
    current = algorithm_data["current"]
    last_step = len(algorithm_data["steps"]) - 1
    infection_step(state["simulation"])
    algorithm_data["simulation_history"] = algorithm_data["simulation_history"][
        :current
    ]
    algorithm_data["simulation_history"].append(
        save_simulation_state(state["simulation"])
    )
    state["patched"] = (
        set(algorithm_data["selected"]) if current == last_step else set()
    )

    return get_algorithm_data()


def previous_algorithm_step():
    """Move the current algorithm page back by one step and restore its simulation."""
    algorithm_data = state["algorithm"]
    if not algorithm_data:
        raise ValueError("an algorithm has not been started")

    if algorithm_data["current"] == 0:
        return get_algorithm_data()

    algorithm_data["current"] -= 1
    restore_simulation_state(
        state["simulation"],
        algorithm_data["simulation_history"][algorithm_data["current"]],
    )
    state["patched"] = set()
    return get_algorithm_data()


def get_algorithm_data():
    """Return the current step for the explanation page."""
    algorithm_data = state["algorithm"]
    if not algorithm_data:
        return {
            "started": False,
            "step": None,
            "current": 0,
            "total": 0,
        }

    current = algorithm_data["current"]
    return {
        "started": True,
        "title": algorithm_data["title"],
        "step": algorithm_data["steps"][current],
        "current": current + 1,
        "total": len(algorithm_data["steps"]),
        "finished": current == len(algorithm_data["steps"]) - 1,
        "can_go_previous": current > 0,
    }


def get_state_data():
    """Create the data sent to the dashboard."""
    network = state["network"]
    simulation = state["simulation"]
    budget = state["budget"]
    benchmarks = run_benchmarks(network, budget)
    node_data = []

    for node in network["nodes"]:
        if node["id"] in state["patched"]:
            node_state = "patched"
        elif node["id"] in simulation["infected"]:
            node_state = "infected"
        else:
            node_state = "healthy"

        node_data.append(
            {
                "id": node["id"],
                "vulnerability": node["vulnerability"],
                "cost": node["cost"],
                "degree": node["degree"],
                "state": node_state,
            }
        )

    benchmark_data = []
    for result in benchmarks:
        benchmark_data.append(
            {
                "name": result["name"],
                "time": result["execution_time_ms"],
                "memory": result["peak_memory_kb"],
                "budget": result["budget_used"],
                "utilization": get_budget_percent_for_dashboard(result),
                "risk": result["risk_reduction"],
            }
        )

    data = {
        "nodes": node_data,
        "edges": network["edges"],
        "time": simulation["time"],
        "infected": len(simulation["infected"]),
        "curve": simulation["infection_curve"],
        "benchmarks": benchmark_data,
        "mode": state["mode"],
        "budget": budget,
    }
    return data


def read_json(handler):
    """Read a JSON request body."""
    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length)
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


def get_budget_percent_for_dashboard(result):
    """Return budget percentage without using a result class."""
    if result["budget"] == 0:
        return 0
    return 100 * result["budget_used"] / result["budget"]


def simulate_once():
    """Run one infection step."""
    infection_step(state["simulation"])


def patch_network(algorithm_name):
    """Patch the network with the selected algorithm."""
    if algorithm_name == "dc":
        selected = divide_and_conquer_patch(state["network"], state["budget"])
    elif algorithm_name == "greedy":
        selected = greedy_patch(state["network"], state["budget"])
    elif algorithm_name == "dp":
        selected = dynamic_programming_patch(state["network"], state["budget"])
    else:
        raise ValueError("unknown algorithm")

    state["patched"] = set(selected)


class DashboardHandler(BaseHTTPRequestHandler):
    """Handle the few HTTP requests used by the dashboard."""

    def send_json(self, data):
        """Send a dictionary as JSON."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        """Handle page and state requests."""
        path = urlparse(self.path).path
        if path == "/":
            body = (ROOT / "dashboard.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/state":
            self.send_json(get_state_data())
        elif path == "/api/algorithm/state":
            self.send_json(get_algorithm_data())
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle reset, simulation, and patch requests."""
        path = urlparse(self.path).path
        try:
            if path == "/api/reset":
                reset_state()
                self.send_json(get_state_data())
            elif path == "/api/simulate":
                simulate_once()
                self.send_json(get_state_data())
            elif path == "/api/configure":
                configure_custom_network(read_json(self))
                self.send_json(get_state_data())
            elif path.startswith("/api/patch/"):
                algorithm_name = path.rsplit("/", 1)[-1]
                patch_network(algorithm_name)
                self.send_json(get_state_data())
            elif path.startswith("/api/algorithm/") and path.endswith("/start"):
                algorithm_name = path.split("/")[3]
                self.send_json(start_algorithm(algorithm_name))
            elif path == "/api/algorithm/next":
                self.send_json(next_algorithm_step())
            elif path == "/api/algorithm/previous":
                self.send_json(previous_algorithm_step())
            else:
                self.send_error(404)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            self.send_error(400, str(error))

    def log_message(self, format_string, *args):
        del format_string, args

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Dashboard running on port {port}")
    server = ThreadingHTTPServer(("0.0.0.0", port), DashboardHandler)
    server.serve_forever()