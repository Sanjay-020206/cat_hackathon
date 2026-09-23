"""Context Fusion Engine (spec section 16).

Fuses machine, operator, task, safety and environment state into one coherent structured
operational context object (shape per spec section 50): current state, risk, risk trend,
contributors, priority.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from app.agents import machine_agent, orchestrator, productivity_agent, safety_agent
from app.ml.risk import RiskInputs, compute_risk, compute_trend


@dataclass
class ContextFusionInput:
    machine_id: str
    operator_id: str
    # current telemetry reading
    cycle_time: float
    idle_time: float
    speed: float
    seatbelt_status: str
    proximity_events: int
    ground_condition: str
    shift_minutes: int
    # operator baseline
    baseline_cycle_time: float
    baseline_idle_time: float
    # recent telemetry window for machine-health trend/deviation (oldest first)
    recent_telemetry: pd.DataFrame
    # counts / flags
    recent_safety_event_count: int = 0
    maintenance_status: str = "Normal"
    task_progress_pct: float = 0.0
    deadline_risk: bool = False
    weather: str = "Clear"


def build_context(inp: ContextFusionInput, risk_history: list[float] | None = None) -> dict:
    safety_result = safety_agent.assess(
        safety_agent.SafetyAgentInput(
            seatbelt_status=inp.seatbelt_status,
            proximity_events=inp.proximity_events,
            recent_safety_event_count=inp.recent_safety_event_count,
            speed=inp.speed,
            shift_minutes=inp.shift_minutes,
            weather=inp.weather,
            ground_condition=inp.ground_condition,
        )
    )
    machine_result = machine_agent.assess(inp.recent_telemetry, maintenance_status=inp.maintenance_status)
    productivity_result = productivity_agent.assess(
        productivity_agent.ProductivityAgentInput(
            current_cycle_time=inp.cycle_time,
            baseline_cycle_time=inp.baseline_cycle_time,
            current_idle_time=inp.idle_time,
            baseline_idle_time=inp.baseline_idle_time,
            task_progress_pct=inp.task_progress_pct,
            deadline_risk=inp.deadline_risk,
        )
    )
    priority = orchestrator.prioritize(safety_result, machine_result, productivity_result)

    hydraulic_trend = machine_result["trends"].get("hydraulic_temp", 0.0)
    risk_inputs = RiskInputs(
        machine_health_score=machine_result["machine_health_score"],
        safety_score=safety_result["safety_score"],
        productivity_score=productivity_result["productivity_score"],
        task_health_score=max(0.0, 100.0 - (0 if not inp.deadline_risk else 20)),
        cycle_time_deviation_pct=productivity_result["cycle_time_deviation_pct"],
        idle_rate_deviation_pct=productivity_result["idle_rate_deviation_pct"],
        proximity_events=inp.proximity_events,
        seatbelt_violation=inp.seatbelt_status != "Fastened",
        hydraulic_temp_trend=hydraulic_trend,
        shift_minutes=inp.shift_minutes,
        ground_condition=inp.ground_condition,
    )
    risk_result = compute_risk(risk_inputs)

    history = (risk_history or []) + [risk_result["risk_score"]]
    trend = compute_trend(history)

    return {
        "machine_id": inp.machine_id,
        "operator_id": inp.operator_id,
        "risk_level": risk_result["risk_level"],
        "risk_score": risk_result["risk_score"],
        "risk_trend": trend,
        "machine_health": round(machine_result["machine_health_score"] / 100.0, 2),
        "safety_score": round(safety_result["safety_score"] / 100.0, 2),
        "productivity_score": round(productivity_result["productivity_score"] / 100.0, 2),
        "task_health": round(risk_inputs.task_health_score / 100.0, 2),
        "contributors": risk_result["contributors"],
        "priority_domain": priority["priority_domain"],
        "priority_reasons": priority["priority_reasons"],
        "agent_details": {
            "safety": safety_result,
            "machine": machine_result,
            "productivity": productivity_result,
        },
    }


class ContextEngine:
    """Stateful wrapper that tracks each machine's risk-score history so risk_trend reflects
    the actual trajectory over time, not just a single reading (spec section 9)."""

    def __init__(self, history_window: int = 12) -> None:
        self.history_window = history_window
        self._risk_history: dict[str, list[float]] = {}

    def process(self, inp: ContextFusionInput) -> dict:
        history = self._risk_history.get(inp.machine_id, [])
        context = build_context(inp, risk_history=history)

        updated = history + [context["risk_score"]]
        self._risk_history[inp.machine_id] = updated[-self.history_window :]
        return context

    def get_risk_history(self, machine_id: str) -> list[float]:
        return list(self._risk_history.get(machine_id, []))

    def reset(self, machine_id: str | None = None) -> None:
        if machine_id is None:
            self._risk_history.clear()
        else:
            self._risk_history.pop(machine_id, None)
