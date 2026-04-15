import time
import threading
import os
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Dict, Optional

from src.utils import ObjMethods
from src.solver import ProductionProblem


@dataclass(frozen=True)
class MethodConfig:
    name: str
    abbreviation: str
    objective_method: str
    graph_suffix: str
    graph_title: str
    print_graph: bool = False
    timeout_sec: Optional[float] = 3600 # time limit for the whole method, None = no limit


@dataclass(frozen=True)
class MethodEvaluationResult:
    method_name: str
    method_abbreviation: str
    objective_method: str
    total_time_sec: float
    value: float
    waste: float
    power: float
    step_timings: Dict[str, float]
    best_weights: Optional[Dict[str, float]] = None # Populated for multi-objective methods only
    timed_out: bool = False


class MethodTimeoutError(Exception):
    """Raised when an evaluation method exceeds its configured timeout."""

    def __init__(self, elapsed_sec: float):
        super().__init__("Method timed out")
        self.elapsed_sec = elapsed_sec


def default_method_configs(example_key: str, example_title: str) -> List[MethodConfig]:
    """ Create standard method configurations for a given example """
    return [
        MethodConfig(
            name="Single Objective: Maximize Value",
            abbreviation="S-V",
            objective_method=ObjMethods.S_VALUE,
            graph_suffix=f"{example_key}_graph_value",
            graph_title=f"{example_title}: Maximize Production Value",
        ),
        MethodConfig(
            name="Single Objective: Minimize Waste",
            abbreviation="S-W",
            objective_method=ObjMethods.S_WASTE,
            graph_suffix=f"{example_key}_graph_waste",
            graph_title=f"{example_title}: Minimize Waste",
        ),
        MethodConfig(
            name="Single Objective: Value with Waste Penalty",
            abbreviation="S-VW",
            objective_method=ObjMethods.S_VALUE_WASTE,
            graph_suffix=f"{example_key}_graph_s_value_waste",
            graph_title=f"{example_title}: Production Penalized with Waste",
        ),
        MethodConfig(
            name="Single Objective: Value with Power Penalty",
            abbreviation="S-VP",
            objective_method=ObjMethods.S_VALUE_POWER,
            graph_suffix=f"{example_key}_graph_s_value_power",
            graph_title=f"{example_title}: Production Penalized with Power",
        ),
        MethodConfig(
            name="Single Objective: Value with Waste and Power Penalty",
            abbreviation="S-VWP",
            objective_method=ObjMethods.S_VALUE_WASTE_POWER,
            graph_suffix=f"{example_key}_graph_s_value_waste_power",
            graph_title=f"{example_title}: Production Penalized with Waste and Power",
        ),
        MethodConfig(
            name="Multi Objective: Value and Waste",
            abbreviation="M-VW",
            objective_method=ObjMethods.M_VALUE_WASTE,
            graph_suffix=f"{example_key}_graph_m_value_waste",
            graph_title=f"{example_title}: Multi-Objective Optimization (Value and Waste)",
        ),
        MethodConfig(
            name="Multi Objective: Value, Waste, and Power",
            abbreviation="M-VWP",
            objective_method=ObjMethods.M_VALUE_WASTE_POWER,
            graph_suffix=f"{example_key}_graph_m_value_waste_power",
            graph_title=f"{example_title}: Multi-Objective Optimization (Value, Waste, and Power)",
        ),
    ]


def _run_step(
    step_name: str,
    func: Callable[[], None],
    announce_interval_sec: int = 60,
    timeout_sec: Optional[float] = None,
) -> float:
    """ Run one evaluation step and print heartbeat updates while it is running """
    error_holder = []

    def target():
        try:
            func()
        # Store error to be re-raised in main thread after join
        except Exception as exc:
            error_holder.append(exc)

    start_time = time.perf_counter()
    worker = threading.Thread(target=target, daemon=True)
    worker.start()

    next_announcement = announce_interval_sec
    while worker.is_alive():
        worker.join(timeout=1.0)
        elapsed = time.perf_counter() - start_time
        if timeout_sec is not None and elapsed >= timeout_sec:
            raise MethodTimeoutError(elapsed)
        if elapsed >= next_announcement:
            print(f"{step_name} in progress... {elapsed:.1f} seconds elapsed")
            next_announcement += announce_interval_sec

    if error_holder:
        raise error_holder[0]

    elapsed = time.perf_counter() - start_time
    print(f"{step_name}: {elapsed:.4f} seconds")
    return elapsed


def _run_method(problem_factory: Callable[[str], ProductionProblem], config: MethodConfig, output_dir: str) -> MethodEvaluationResult:
    problem = problem_factory(config.objective_method)
    save_path = f"{output_dir}/{config.graph_suffix}"

    total_start = time.perf_counter()
    deadline = (total_start + config.timeout_sec) if config.timeout_sec is not None else None
    step_timings: Dict[str, float] = {}

    def remaining_timeout() -> Optional[float]:
        if deadline is None:
            return None
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            raise MethodTimeoutError(time.perf_counter() - total_start)
        return remaining

    # Store timings for each evaluation step
    step_timings["Optimization"] = _run_step("Optimization", problem.optimize, timeout_sec=remaining_timeout())
    step_timings["Graph creation"] = _run_step("Graph creation", problem.create_graph, timeout_sec=remaining_timeout())
    if config.print_graph:
        step_timings["Print graph"] = _run_step("Print graph", problem.print_graph, timeout_sec=remaining_timeout())
    step_timings["Visualization"] = _run_step(
        "Visualization",
        lambda: problem.visualize_graph(save_path, config.graph_title),
        timeout_sec=remaining_timeout(),
    )

    # Obtain result metrics after optimization and graph creation
    value = problem.get_value()
    waste = problem.get_waste()
    power = problem.get_power_consumption()
    best_weights = problem.get_best_weights()

    total_elapsed = time.perf_counter() - total_start
    print(f"Total time taken: {total_elapsed:.4f} seconds")
    return MethodEvaluationResult(config.name, config.abbreviation, config.objective_method, total_elapsed, value, waste, power, step_timings, best_weights)


def _safe_json_value(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _result_to_json_dict(index: int, total: int, result: MethodEvaluationResult) -> Dict[str, object]:
    return {
        "index": index,
        "total": total,
        "method_name": result.method_name,
        "method_abbreviation": result.method_abbreviation,
        "objective_method": result.objective_method,
        "status": "timeout" if result.timed_out else "completed",
        "timed_out": result.timed_out,
        "total_time_sec": _safe_json_value(result.total_time_sec),
        "step_timings": {k: _safe_json_value(v) for k, v in result.step_timings.items()},
        "value": _safe_json_value(result.value),
        "waste": _safe_json_value(result.waste),
        "power": _safe_json_value(result.power),
        "best_weights": result.best_weights,
    }


def _write_json_snapshot(log_path: str, payload: Dict[str, object]):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    temp_path = f"{log_path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(temp_path, log_path)


def run_evaluation(problem_factory: Callable[[str], ProductionProblem], method_configs: List[MethodConfig], evaluation_name: str, output_dir: str = "./images/eval", log_path: Optional[str] = None) -> List[MethodEvaluationResult]:
    """ Run the configured evaluation methods and return per-method metrics and timings. """
    
    # Ensure output folder exists for method graph images
    os.makedirs(output_dir, exist_ok=True)

    # Prepare JSON snapshot log for real-time writing if a path is provided
    log_payload = None
    if log_path:
        log_payload = {
            "evaluation_name": evaluation_name,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "output_dir": output_dir,
            "total_methods": len(method_configs),
            "methods_completed": 0,
            "methods": [],
            "overall_total_time_sec": None,
            "completed_at": None,
        }
        _write_json_snapshot(log_path, log_payload)

    print(f"\n\nRunning {evaluation_name}...")
    overall_start = time.perf_counter()
    results: List[MethodEvaluationResult] = []
    
    # Loop through each method
    total_methods = len(method_configs)
    for index, config in enumerate(method_configs, start=1):
        print(f"\n{index}/{total_methods}. Optimizing with {config.name} ({config.abbreviation})...")
        try:
            result = _run_method(problem_factory, config, output_dir)
        except MethodTimeoutError as exc:
            print(f"  [TIMEOUT] {config.name} ({config.abbreviation}) exceeded {config.timeout_sec}s — skipping.")
            timeout_value = float(config.timeout_sec) if config.timeout_sec is not None else float(exc.elapsed_sec)
            result = MethodEvaluationResult(
                method_name=config.name,
                method_abbreviation=config.abbreviation,
                objective_method=config.objective_method,
                total_time_sec=timeout_value,
                value=float("nan"),
                waste=float("nan"),
                power=float("nan"),
                step_timings={},
                timed_out=True,
            )

        results.append(result)
        if log_payload is not None:
            log_payload["methods"].append(_result_to_json_dict(index, total_methods, result))
            log_payload["methods_completed"] = len(log_payload["methods"])
            _write_json_snapshot(log_path, log_payload)

    # Summarize time taken for each method
    print("\nTiming summary:")
    for result in results:
        step_summary = ", ".join(
            f"{step_name}: {duration:.4f}s" for step_name, duration in result.step_timings.items()
        )
        print(f"- {result.method_abbreviation} ({result.method_name}) Total: {result.total_time_sec:.4f}s [{step_summary}]")

    # Summarize overall time taken
    overall_elapsed = time.perf_counter() - overall_start
    print(f"Overall total time: {overall_elapsed:.4f} seconds")
    print(f"{evaluation_name} complete!")

    if log_payload is not None:
        log_payload["overall_total_time_sec"] = overall_elapsed
        log_payload["completed_at"] = datetime.now().isoformat(timespec="seconds")
        _write_json_snapshot(log_path, log_payload)
        print(f"Evaluation log written to {log_path}")

    return results