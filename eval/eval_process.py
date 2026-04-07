import time
import threading
from dataclasses import dataclass
from typing import Callable, List, Dict, Tuple

from src.common import ObjMethods
from src.solver import ProductionProblem


@dataclass(frozen=True)
class MethodConfig:
    label: str
    objective_method: str
    graph_suffix: str
    graph_title: str
    print_graph: bool = False


def default_method_configs(example_key: str, example_title: str) -> List[MethodConfig]:
    """ Create standard method configurations for a given example """
    return [
        MethodConfig(
            label="1. Optimizing for Maximum Production Value...",
            objective_method=ObjMethods.S_VALUE,
            graph_suffix=f"{example_key}_graph_value",
            graph_title=f"{example_title}: Maximize Production Value",
        ),
        MethodConfig(
            label="2. Optimizing for Minimum Waste...",
            objective_method=ObjMethods.S_WASTE,
            graph_suffix=f"{example_key}_graph_waste",
            graph_title=f"{example_title}: Minimize Waste",
        ),
        MethodConfig(
            label="3. Optimizing for Production Value with Waste Penalty with Single Objective Function...",
            objective_method=ObjMethods.S_VALUE_WASTE,
            graph_suffix=f"{example_key}_graph_s_value_waste",
            graph_title=f"{example_title}: Production Penalized with Waste",
        ),
        MethodConfig(
            label="4. Optimizing for Production Value and Waste with Multi-Objective Optimization (Pareto Front)...",
            objective_method=ObjMethods.M_VALUE_WASTE,
            graph_suffix=f"{example_key}_graph_m_value_waste",
            graph_title=f"{example_title}: Multi-Objective Optimization (Value and Waste)",
        ),
    ]


def _run_step(step_name: str, func: Callable[[], None], announce_interval_sec: int = 60) -> float:
    """Run one evaluation step and print heartbeat updates while it is running."""
    error_holder = []

    def target():
        try:
            func()
        except Exception as exc:  # Re-raised below in main thread.
            error_holder.append(exc)

    start_time = time.perf_counter()
    worker = threading.Thread(target=target, daemon=True)
    worker.start()

    next_announcement = announce_interval_sec
    while worker.is_alive():
        worker.join(timeout=1.0)
        elapsed = time.perf_counter() - start_time
        if elapsed >= next_announcement:
            print(f"{step_name} in progress... {elapsed:.1f} seconds elapsed")
            next_announcement += announce_interval_sec

    if error_holder:
        raise error_holder[0]

    elapsed = time.perf_counter() - start_time
    print(f"{step_name}: {elapsed:.4f} seconds")
    return elapsed


def _run_method(problem_factory: Callable[[str], ProductionProblem], config: MethodConfig, output_dir: str) -> Tuple[str, float, Dict[str, float]]:
    print(f"\n{config.label}")
    problem = problem_factory(config.objective_method)
    save_path = f"{output_dir}/{config.graph_suffix}"

    total_start = time.perf_counter()
    step_timings: Dict[str, float] = {}

    # Store timings for each step
    step_timings["Optimization"] = _run_step("Optimization", problem.optimize)
    step_timings["Graph creation"] = _run_step("Graph creation", problem.create_graph)
    if config.print_graph:
        step_timings["Print graph"] = _run_step("Print graph", problem.print_graph)
    step_timings["Visualization"] = _run_step(
        "Visualization",
        lambda: problem.visualize_graph(save_path, config.graph_title),
    )

    total_elapsed = time.perf_counter() - total_start
    print(f"Total time taken: {total_elapsed:.4f} seconds")
    return config.label, total_elapsed, step_timings


def run_evaluation(
    problem_factory: Callable[[str], ProductionProblem],
    method_configs: List[MethodConfig],
    evaluation_name: str,
    output_dir: str = "./images/eval",
) -> None:
    """Run the configured evaluation methods and print per-step and summary timing."""
    print(f"\n\nRunning {evaluation_name}...")
    overall_start = time.perf_counter()
    results = [_run_method(problem_factory, config, output_dir) for config in method_configs]

    print("\nTiming summary:")
    for label, total_elapsed, step_timings in results:
        step_summary = ", ".join(
            f"{step_name}: {duration:.4f}s" for step_name, duration in step_timings.items()
        )
        print(f"- {label} Total: {total_elapsed:.4f}s [{step_summary}]")

    overall_elapsed = time.perf_counter() - overall_start
    print(f"Overall total time: {overall_elapsed:.4f} seconds")
    print(f"{evaluation_name} complete!")
