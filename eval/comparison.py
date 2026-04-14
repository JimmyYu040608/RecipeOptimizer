from typing import List, Dict
import os
import matplotlib.pyplot as plt
import numpy as np

from eval.eval_process import MethodEvaluationResult


METRIC_KEYS = ["value", "waste", "power", "time"]
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


def _raw_metrics(result: MethodEvaluationResult) -> Dict[str, float]:
    return {
        "value": result.value,
        "waste": result.waste,
        "power": result.power,
        "time": result.total_time_sec,
    }


def _normalize_series(values: List[float]) -> List[float]:
    # Scale by metric maximum so the highest bar fits while preserving baseline separation.
    clean = [v for v in values if np.isfinite(v)]
    if not clean:
        return [0.0 for _ in values]
    v_max = max(clean)
    if abs(v_max) < 1e-12:
        return [0.0 if np.isfinite(v) else 0.0 for v in values]
    return [(v / v_max) if np.isfinite(v) else 0.0 for v in values]


def _format_raw_value(metric_key: str, value: float) -> str:
    if not np.isfinite(value):
        return "N/A"
    if metric_key == "time":
        return f"{value:.2f}s"
    return f"{value:.1f}"


def plot_comparison(results: List[MethodEvaluationResult], title: str, output_path: str = None):
    """ Plot value, waste, power, and time on one normalized y-axis with raw values shown on bars. """
    if not results:
        return

    method_ticks = [r.method_abbreviation for r in results]
    x = np.arange(len(results), dtype=float)
    width = 0.18
    offsets = {
        "value": -1.5 * width,
        "waste": -0.5 * width,
        "power": 0.5 * width,
        "time": 1.5 * width,
    }

    raw_by_metric = {k: [_raw_metrics(r)[k] for r in results] for k in METRIC_KEYS}
    norm_by_metric = {k: _normalize_series(raw_by_metric[k]) for k in METRIC_KEYS}

    fig, ax = plt.subplots(figsize=(12, 6))

    for metric_key in METRIC_KEYS:
        bars = ax.bar(
            x + offsets[metric_key],
            norm_by_metric[metric_key],
            width,
            label=METRIC_LABELS[metric_key],
            color=METRIC_COLORS[metric_key],
            alpha=0.9,
        )
        for idx, bar in enumerate(bars):
            raw_val = raw_by_metric[metric_key][idx]
            label = _format_raw_value(metric_key, raw_val)
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
    ax.legend(loc="upper left", ncols=2)

    plt.tight_layout()
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Saved comparison plot to {output_path}")
    # plt.show()