"""Productivity Agent: cycle time, idle, load, task progress and ETA -> a structured
productivity assessment against the operator's own historical baseline (spec section 12 / 33)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProductivityAgentInput:
    current_cycle_time: float
    baseline_cycle_time: float
    current_idle_time: float
    baseline_idle_time: float
    task_progress_pct: float
    deadline_risk: bool


def _pct_deviation(current: float, baseline: float) -> float:
    if baseline <= 0:
        return 0.0
    return (current - baseline) / baseline


def assess(inputs: ProductivityAgentInput) -> dict:
    cycle_dev = _pct_deviation(inputs.current_cycle_time, inputs.baseline_cycle_time)
    idle_dev = _pct_deviation(inputs.current_idle_time, inputs.baseline_idle_time)

    reasons: list[str] = []
    score = 100.0

    if cycle_dev > 0.1:
        score -= min(35, cycle_dev * 100)
        reasons.append(f"Cycle time is {round(cycle_dev * 100)}% above operator baseline.")

    if idle_dev > 0.1:
        score -= min(25, idle_dev * 80)
        reasons.append(f"Idle time is {round(idle_dev * 100)}% above operator baseline.")

    if inputs.deadline_risk:
        score -= 15
        reasons.append("Task is at risk of missing its deadline.")

    score = max(0.0, min(100.0, score))
    if score >= 80:
        state = "Normal"
    elif score >= 55:
        state = "Deviating"
    else:
        state = "Underperforming"

    return {
        "productivity_score": round(score, 1),
        "productivity_state": state,
        "cycle_time_deviation_pct": round(cycle_dev, 3),
        "idle_rate_deviation_pct": round(idle_dev, 3),
        "reasons": reasons,
    }
