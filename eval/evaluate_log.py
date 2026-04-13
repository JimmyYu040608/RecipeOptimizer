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
    v_min = min(clean)
    v_max = max(clean)
    if abs(v_max - v_min) < 1e-12:
        return [1.0 if np.isfinite(v) else 0.0 for v in values]
    return [((v - v_min) / (v_max - v_min)) if np.isfinite(v) else 0.0 for v in values]


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


def _plot_multi_metric_bars(results: List[MethodEvaluationResult], metric_keys: List[str], title: str, output_path: str):
    if not results:
        return

    method_ticks = [r.method_abbreviation for r in results]
    x = np.arange(len(results), dtype=float)
    width = 0.18 if len(metric_keys) >= 3 else 0.28

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
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper left", ncols=min(len(metric_keys), 3))

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


if __name__ == "__main__":
    main()
