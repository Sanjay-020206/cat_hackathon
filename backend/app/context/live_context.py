"""Bridges the live telemetry stream (scripted demo or random simulation) to the Context
Engine + NBA Engine, so each WebSocket tick carries a real-time recommendation computed
from the actual live reading -- not a separate, possibly-stale REST lookup against
historical DB data (spec section 26-28: simulator -> data adapter -> context engine ->
risk engine -> NBA, all live).
"""
from __future__ import annotations

from collections import deque

import pandas as pd

from app.context.context_engine import ContextEngine, ContextFusionInput, build_context
from app.context.explain import build_explanation
from app.context.nba_engine import next_best_action

DEFAULT_BASELINE_CYCLE_TIME = 44.0
DEFAULT_BASELINE_IDLE_TIME = 8.0
WINDOW_SIZE = 10


class LiveContextProcessor:
    def __init__(self) -> None:
        self.engine = ContextEngine()
        self._windows: dict[str, deque] = {}
        self._tick_counts: dict[str, int] = {}

    def process_reading(self, reading: dict) -> dict:
        machine_id = reading["machine_id"]
        window = self._windows.setdefault(machine_id, deque(maxlen=WINDOW_SIZE))
        window.append(reading)
        self._tick_counts[machine_id] = self._tick_counts.get(machine_id, 0) + 1

        recent_df = pd.DataFrame(
            [
                {
                    "engine_temp": r["engine_temp"],
                    "hydraulic_pressure": r["hydraulic_pressure"],
                    "hydraulic_temp": r["hydraulic_temp"],
                    "engine_load": r["engine_load"],
                }
                for r in window
            ]
        )

        inp = ContextFusionInput(
            machine_id=machine_id,
            operator_id=reading["operator_id"],
            cycle_time=reading["cycle_time"],
            idle_time=reading["idle_time"],
            speed=reading["speed"],
            seatbelt_status=reading["seatbelt_status"],
            proximity_events=reading.get("proximity_events", 0),
            ground_condition=reading.get("ground_condition", "Dry"),
            shift_minutes=self._tick_counts[machine_id] * 5,
            baseline_cycle_time=DEFAULT_BASELINE_CYCLE_TIME,
            baseline_idle_time=DEFAULT_BASELINE_IDLE_TIME,
            recent_telemetry=recent_df,
            recent_safety_event_count=sum(r.get("proximity_events", 0) for r in window),
            weather=reading.get("weather", "Clear"),
        )

        context = self.engine.process(inp)
        nba = next_best_action(context)
        explanation = build_explanation(context, nba)

        return {
            "risk_level": context["risk_level"],
            "risk_score": context["risk_score"],
            "risk_trend": context["risk_trend"],
            "contributors": context["contributors"],
            "next_best_action": nba,
            "explanation": explanation,
        }

    def reset(self, machine_id: str | None = None) -> None:
        if machine_id is None:
            self._windows.clear()
            self._tick_counts.clear()
            self.engine.reset()
        else:
            self._windows.pop(machine_id, None)
            self._tick_counts.pop(machine_id, None)
            self.engine.reset(machine_id)
