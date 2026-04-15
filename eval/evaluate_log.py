import os
import json
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np

from eval.eval_process import MethodEvaluationResult
from src.utils import to_float


METHOD_GRAPH_ROOT = "./images/eval"
COMPARISON_ROOT = "./images/eval/comparison"

METRIC_LABELS = {
    "value": "Value",
    "waste": "Waste",
    "power": "Power",
    "time": "Time",
}

METRIC_COLORS = {
    "value": "#3A86FF",
    "waste": "#FB5607",
    "power": "#8338EC",
    "time": "#2A9D8F",
}

SINGLE_METHOD_IDS = {
    "s_value",
    "s_waste",
    "s_value_waste",
    "s_value_power",
    "s_value_waste_power",
}

PAIRED_METHODS = [
    ("s_value_waste", "m_value_waste", "Value+Waste"),
    ("s_value_waste_power", "m_value_waste_power", "Value+Waste+Power"),
]

ALL_METHODS = [
    "s_value",
    "s_waste",
    "s_value_waste",
    "s_value_power",
    "s_value_waste_power",
    "m_value_waste",
    "m_value_waste_power",
]


def parse_evaluation_log_json(log_path: str) -> tuple[str, List[MethodEvaluationResult]]:
    """ Parse one log.json into MethodEvaluationResult rows """
    if not os.path.exists(log_path):
        return "", []

    with open(log_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    evaluation_name = str(payload.get("evaluation_name", "Evaluation"))
    methods = payload.get("methods", [])
    results: List[MethodEvaluationResult] = []

    for item in methods:
        result = MethodEvaluationResult(
            method_name=str(item.get("method_name", "Unknown Method")),
            method_abbreviation=str(item.get("method_abbreviation", "N/A")),
            objective_method=str(item.get("objective_method", "from_log")),
            total_time_sec=to_float(item.get("total_time_sec")),
            value=to_float(item.get("value")),
            waste=to_float(item.get("waste")),
            power=to_float(item.get("power")),
            step_timings={k: to_float(v) for k, v in (item.get("step_timings") or {}).items()},
            best_weights=item.get("best_weights"),
            timed_out=bool(item.get("timed_out", False)),
        )
        results.append(result)

    return evaluation_name, results


def _title_from_evaluation_name(evaluation_name: str) -> str:
    base = evaluation_name.replace(" Evaluation", "").strip()
    return f"{base}: Value, Waste, Power, and Time by Method"


def _base_problem_title(evaluation_name: str) -> str:
    return evaluation_name.replace(" Evaluation", "").strip()


def _normalize_series(values: List[float]) -> List[float]:
    clean = [v for v in values if np.isfinite(v)]
    if not clean:
        return [0.0 for _ in values]
    v_max = max(clean)
    if abs(v_max) < 1e-12:
        return [0.0 if np.isfinite(v) else 0.0 for v in values]
    return [(v / v_max) if np.isfinite(v) else 0.0 for v in values]


def _format_raw(metric_key: str, value: float) -> str:
    if not np.isfinite(value):
        return "N/A"
    if metric_key == "time":
        return f"{value:.2f}s"
    return f"{value:.1f}"


def _metric_values(results: List[MethodEvaluationResult], metric_key: str) -> List[float]:
    if metric_key == "value":
        return [r.value for r in results]
    if metric_key == "waste":
        return [r.waste for r in results]
    if metric_key == "power":
        return [r.power for r in results]
    if metric_key == "time":
        return [r.total_time_sec for r in results]
    raise ValueError(f"Unsupported metric key: {metric_key}")


def _plot_multi_metric_bars(results: List[MethodEvaluationResult], metric_keys: List[str], title: str, output_path: str, bar_width: Optional[float] = None):
    if not results:
        return

    method_ticks = [r.method_abbreviation for r in results]
    is_two_method_plot = len(results) == 2
    if is_two_method_plot:
        group_spacing = 0.10 if len(metric_keys) >= 3 else 0.14
        x = np.array([0.0, group_spacing], dtype=float)
    else:
        x = np.arange(len(results), dtype=float)
    
    if bar_width is None:
        if is_two_method_plot:
            width = 0.025 if len(metric_keys) >= 3 else 0.06
        else:
            width = 0.18 if len(metric_keys) >= 3 else 0.28
    else:
        width = bar_width

    if len(metric_keys) == 3:
        offsets = {
            metric_keys[0]: -width,
            metric_keys[1]: 0.0,
            metric_keys[2]: width,
        }
    elif len(metric_keys) == 2:
        offsets = {
            metric_keys[0]: -0.5 * width,
            metric_keys[1]: 0.5 * width,
        }
    else:
        offsets = {metric_keys[0]: 0.0}

    raw_by_metric = {k: _metric_values(results, k) for k in metric_keys}
    norm_by_metric = {k: _normalize_series(raw_by_metric[k]) for k in metric_keys}

    if is_two_method_plot:
        fig, ax = plt.subplots(figsize=(4.2, 4.8))
        fig.subplots_adjust(left=0.18, right=0.96, top=0.88, bottom=0.16)
    else:
        fig, ax = plt.subplots(figsize=(12, 6))

    for metric_key in metric_keys:
        bars = ax.bar(
            x + offsets[metric_key],
            norm_by_metric[metric_key],
            width,
            label=METRIC_LABELS[metric_key],
            color=METRIC_COLORS[metric_key],
            alpha=0.9,
        )
        for idx, bar in enumerate(bars):
            label = _format_raw(metric_key, raw_by_metric[metric_key][idx])
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.015,
                label,
                ha="center",
                va="bottom",
                fontsize=8,
                rotation=90,
            )

    ax.set_title(title)
    ax.set_xlabel("Method")
    ax.set_ylabel("Normalized Metric Value (0-1)")
    ax.set_xticks(x)
    ax.set_xticklabels(method_ticks)
    ax.set_ylim(0, 1.22)
    if is_two_method_plot:
        half_group_span = ((len(metric_keys) - 1) * width) + (width * 0.55)
        ax.set_xlim(x[0] - half_group_span, x[1] + half_group_span)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper left", ncols=min(len(metric_keys), 3))

    if not is_two_method_plot:
        plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved comparison plot to {output_path}")


def _plot_time_bars_with_timeout_handling(results: List[MethodEvaluationResult], title: str, output_path: str):
    """Plot all-method time comparison with timeout methods shown as zero-height bars."""
    if not results:
        return

    labels = [r.method_abbreviation for r in results]
    times = np.array([r.total_time_sec if np.isfinite(r.total_time_sec) else np.nan for r in results], dtype=float)
    timed_out = np.array([r.timed_out for r in results], dtype=bool)

    non_timeout = times[np.isfinite(times) & (~timed_out)]
    if non_timeout.size == 0:
        return

    # Timeout bars are intentionally set to 0 so finished methods remain readable.
    display_times = np.where(timed_out, 0.0, np.where(np.isfinite(times), times, 0.0))
    y_top = max(np.max(non_timeout) * 1.18, np.max(non_timeout) + 0.5)
    label_pad = max(y_top * 0.02, 0.05)
    timeout_label_y = max(y_top * 0.03, 0.08)

    x = np.arange(len(results), dtype=float)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(x, display_times, width=0.6, color=METRIC_COLORS["time"], alpha=0.9)

    for idx, bar in enumerate(bars):
        raw = times[idx]
        if timed_out[idx]:
            label = "TIMEOUT"
            y_text = timeout_label_y
        elif not np.isfinite(raw):
            label = "N/A"
            y_text = timeout_label_y
        else:
            label = f"{raw:.2f}s"
            y_text = bar.get_height() + label_pad

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y_text,
            label,
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=90,
        )

    ax.set_title(title)
    ax.set_xlabel("Method")
    ax.set_ylabel("Time (seconds)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, y_top if y_top > 0 else 1)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved comparison plot to {output_path}")


def _collect_runtime_by_example(log_paths: List[str]) -> tuple[List[str], List[str], Dict[str, List[float]], Dict[str, List[bool]]]:
    """Collect runtime per method for every example log."""
    desired_problem_order = [
        "small_example",
        "medium_example",
        "single_large_example",
        "example_5",
    ]
    ordered_logs: List[str] = []
    remaining_logs: List[str] = []
    problem_key_by_log = {os.path.basename(os.path.dirname(p)): p for p in log_paths}
    for key in desired_problem_order:
        p = problem_key_by_log.get(key)
        if p is not None:
            ordered_logs.append(p)
    for p in log_paths:
        if p not in ordered_logs:
            remaining_logs.append(p)

    example_names: List[str] = []
    method_labels: Dict[str, str] = {}
    time_by_method: Dict[str, List[float]] = {m: [] for m in ALL_METHODS}
    timeout_by_method: Dict[str, List[bool]] = {m: [] for m in ALL_METHODS}

    for log_path in ordered_logs + remaining_logs:
        evaluation_name, results = parse_evaluation_log_json(log_path)
        if not results:
            continue

        example_names.append(_base_problem_title(evaluation_name))
        by_objective = {r.objective_method: r for r in results}

        for method_id in ALL_METHODS:
            r = by_objective.get(method_id)
            if r is None:
                time_by_method[method_id].append(np.nan)
                timeout_by_method[method_id].append(False)
                continue

            method_labels[method_id] = r.method_abbreviation
            value = r.total_time_sec if np.isfinite(r.total_time_sec) else np.nan
            time_by_method[method_id].append(value)
            timeout_by_method[method_id].append(r.timed_out)

    method_order = [m for m in ALL_METHODS if any(np.isfinite(v) for v in time_by_method[m])]
    display_method_labels = [method_labels.get(m, m) for m in method_order]

    filtered_times = {m: time_by_method[m] for m in method_order}
    filtered_timeouts = {m: timeout_by_method[m] for m in method_order}
    return example_names, display_method_labels, filtered_times, filtered_timeouts


def _plot_runtime_all_examples(log_paths: List[str], output_path: str):
    """Create one grouped bar chart for runtime of all methods over all examples."""
    example_names, method_labels, time_by_method, timeout_by_method = _collect_runtime_by_example(log_paths)
    if not example_names or not method_labels:
        return

    method_ids = list(time_by_method.keys())
    method_count = len(method_ids)
    example_count = len(example_names)

    x = np.arange(method_count, dtype=float)
    width = min(0.8 / max(example_count, 1), 0.16)
    offsets = (np.arange(example_count, dtype=float) - (example_count - 1) / 2.0) * width

    fig, ax = plt.subplots(figsize=(max(12, method_count * 1.4), 6.8))
    cmap = plt.get_cmap("tab10")

    visible_values: List[float] = []
    for method_id, values in time_by_method.items():
        for idx, v in enumerate(values):
            is_timeout = idx < len(timeout_by_method[method_id]) and timeout_by_method[method_id][idx]
            if is_timeout:
                continue
            if np.isfinite(v):
                visible_values.append(v)
    if not visible_values:
        plt.close(fig)
        return

    y_max = max(visible_values)
    target_bar_ratio = 0.90
    y_top = max(y_max / target_bar_ratio, y_max + 0.1)
    timeout_bar_height = max(y_max * 0.006, 0.02)
    timeout_label_y = timeout_bar_height + max(y_max * 0.006, 0.02)
    value_label_pad = max(y_max * 0.015, 0.05)

    for ex_idx, example_name in enumerate(example_names):
        legend_drawn = False
        color = cmap(ex_idx % 10)
        for method_idx, method_id in enumerate(method_ids):
            if ex_idx >= len(time_by_method[method_id]):
                continue

            raw_value = time_by_method[method_id][ex_idx]
            is_timeout = timeout_by_method[method_id][ex_idx] if ex_idx < len(timeout_by_method[method_id]) else False
            x_pos = x[method_idx] + offsets[ex_idx]

            if is_timeout:
                label = example_name if not legend_drawn else None
                bars = ax.bar(
                    [x_pos],
                    [timeout_bar_height],
                    width=width,
                    label=label,
                    color=color,
                    alpha=0.88,
                    edgecolor="black",
                    linewidth=0.4,
                )
                bars[0].set_hatch("//")
                legend_drawn = True
                ax.text(
                    x_pos,
                    timeout_label_y,
                    "TIMEOUT",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    rotation=90,
                    color=color,
                    fontweight="bold",
                )
                continue

            if not np.isfinite(raw_value):
                continue

            label = example_name if not legend_drawn else None
            bars = ax.bar(
                [x_pos],
                [raw_value],
                width=width,
                label=label,
                color=color,
                alpha=0.88,
                edgecolor="black",
                linewidth=0.4,
            )
            legend_drawn = True

            bar = bars[0]
            value_label_y = min(raw_value + value_label_pad, y_top * 0.98)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value_label_y,
                f"{raw_value:.2f}s",
                ha="center",
                va="bottom",
                fontsize=8,
                rotation=90,
            )

    ax.set_ylim(0, y_top if y_top > 0 else 1)
    ax.set_title("Runtime Comparison Across All Methods and Examples")
    ax.set_xlabel("Method")
    ax.set_ylabel("Time (seconds)")
    ax.set_xticks(x)
    ax.set_xticklabels(method_labels)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper left", ncols=2 if example_count >= 4 else 1)

    timeout_note = "Timeout runs are tiny hatched bars at baseline with TIMEOUT labels"
    ax.text(
        0.99,
        0.98,
        timeout_note,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none", "pad": 2},
    )

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved comparison plot to {output_path}")


def _find_result_by_objective(results: List[MethodEvaluationResult], objective_method: str) -> Optional[MethodEvaluationResult]:
    for r in results:
        if r.objective_method == objective_method:
            return r
    return None


def _discover_json_logs(root: str) -> List[str]:
    """ Discover every log.json under problem subfolders dynamically """
    logs = []
    if not os.path.isdir(root):
        return logs

    for entry in os.scandir(root):
        if not entry.is_dir():
            continue
        if entry.name == "comparison":
            continue
        candidate = os.path.join(entry.path, "log.json")
        if os.path.isfile(candidate):
            logs.append(candidate)
            continue

    logs.sort()
    return logs


def plot_from_log(log_path: str):
    """Parse one JSON log and generate all requested comparison charts for that problem."""
    problem_key = os.path.basename(os.path.dirname(log_path))
    problem_title_prefix = ""

    evaluation_name, results = parse_evaluation_log_json(log_path)
    if not results:
        print(f"Skip {problem_key}: no parsable result rows in {log_path}")
        return

    problem_title_prefix = _base_problem_title(evaluation_name)

    # 1) Global comparison: value/waste/power only (no time)
    _plot_multi_metric_bars(
        results,
        metric_keys=["value", "waste", "power"],
        title=f"{problem_title_prefix}: Value, Waste, and Power by Method",
        output_path=f"{COMPARISON_ROOT}/{problem_key}_comparison.png",
    )

    # 2) Global comparison: time only with timeout handling
    _plot_time_bars_with_timeout_handling(
        results,
        title=f"{problem_title_prefix}: Time by Method",
        output_path=f"{COMPARISON_ROOT}/{problem_key}_time_comparison.png",
    )

    # 3) Local comparison: all single-objective methods (no time)
    single_results = [r for r in results if r.objective_method in SINGLE_METHOD_IDS]
    if len(single_results) >= 2:
        _plot_multi_metric_bars(
            single_results,
            metric_keys=["value", "waste", "power"],
            title=f"{problem_title_prefix}: Single-Objective Methods (Value/Waste/Power)",
            output_path=f"{COMPARISON_ROOT}/{problem_key}_single_comparison.png",
        )

    # 4) Local paired comparisons: single vs multi for same objective set
    for single_id, multi_id, label in PAIRED_METHODS:
        single_method = _find_result_by_objective(results, single_id)
        multi_method = _find_result_by_objective(results, multi_id)
        if single_method is None or multi_method is None:
            continue
        pair_results = [single_method, multi_method]
        slug = label.lower().replace("+", "_").replace(" ", "_")
        _plot_multi_metric_bars(
            pair_results,
            metric_keys=["value", "waste", "power"],
            title=f"{problem_title_prefix}: {label} (Single vs Multi)",
            output_path=f"{COMPARISON_ROOT}/{problem_key}_pair_{slug}.png",
        )


def main():
    """ Rebuild per-problem comparison plots from all discovered JSON evaluation logs """
    os.makedirs(COMPARISON_ROOT, exist_ok=True)

    logs = _discover_json_logs(METHOD_GRAPH_ROOT)
    if not logs:
        print(f"No log.json found under {METHOD_GRAPH_ROOT}")
        return

    for log_path in logs:
        plot_from_log(log_path)

    _plot_runtime_all_examples(
        logs,
        output_path=f"{COMPARISON_ROOT}/all_examples_runtime_comparison.png",
    )


if __name__ == "__main__":
    main()
