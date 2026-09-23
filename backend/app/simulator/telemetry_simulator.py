"""
Live telemetry simulator.

Emits telemetry on the same internal data contract (spec section 49) regardless of
whether it is driven by the scripted demo scenario (deterministic, for reliable demos)
or by randomized live simulation (for open-ended exploration). Downstream code (backend,
ML, context engine) never depends on which source produced the reading -- this is the
"hardware abstraction" data-adapter boundary described in the spec (section 27).
"""
from __future__ import annotations

import itertools
import random
from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any

from app.simulator.scenario import DEMO_MACHINE_ID, DEMO_OPERATOR_ID, STAGES, stage_to_telemetry


class TelemetrySimulator:
    """Generates a stream of telemetry dicts. Call `next_reading()` repeatedly, e.g. from a
    WebSocket loop or a polling task. Two modes:

    - scripted (default): deterministically replays the 10-stage demo scenario, one stage
      per call, then holds at the final ("improved") state.
    - random: generates continuous randomized-but-plausible telemetry for a given machine/operator,
      for open-ended live exploration outside the scripted demo.
    """

    def __init__(self, mode: str = "scripted", seed: int | None = 7) -> None:
        if mode not in ("scripted", "random"):
            raise ValueError("mode must be 'scripted' or 'random'")
        self.mode = mode
        self._rng = random.Random(seed)
        self._start_time = datetime.now()
        self._stage_iter: Iterator[int] = itertools.chain(range(len(STAGES)), itertools.repeat(len(STAGES) - 1))
        self._tick = 0

    def reset(self) -> None:
        self._start_time = datetime.now()
        self._stage_iter = itertools.chain(range(len(STAGES)), itertools.repeat(len(STAGES) - 1))
        self._tick = 0

    def next_reading(self) -> dict[str, Any]:
        self._tick += 1
        if self.mode == "scripted":
            return self._next_scripted()
        return self._next_random()

    def _next_scripted(self) -> dict[str, Any]:
        stage_idx = next(self._stage_iter)
        stage = STAGES[stage_idx]
        ts = self._start_time + timedelta(minutes=stage.time_offset_min)
        reading = stage_to_telemetry(stage, ts.isoformat())
        reading["stage_index"] = stage_idx
        reading["stage_count"] = len(STAGES)
        return reading

    def _next_random(self) -> dict[str, Any]:
        rng = self._rng
        ts = datetime.now()
        reading = {
            "timestamp": ts.isoformat(),
            "machine_id": DEMO_MACHINE_ID,
            "operator_id": DEMO_OPERATOR_ID,
            "engine_rpm": int(rng.uniform(1400, 1900)),
            "engine_temp": round(rng.uniform(75, 92), 1),
            "hydraulic_pressure": round(rng.uniform(22, 32), 1),
            "hydraulic_temp": round(rng.uniform(58, 78), 1),
            "fuel_level": round(max(5.0, 90 - self._tick * 0.05), 1),
            "fuel_rate": round(rng.uniform(3.5, 7.5), 2),
            "engine_load": round(rng.uniform(40, 85), 1),
            "speed": round(rng.uniform(2.0, 5.5), 1),
            "cycle_time": round(rng.uniform(38, 60), 1),
            "idle_time": round(rng.uniform(4, 20), 1),
            "load_cycles": int(rng.uniform(4, 12)),
            "seatbelt_status": "Fastened" if rng.random() > 0.05 else "Unfastened",
            "proximity_alert": rng.random() < 0.08,
            "proximity_events": 1 if rng.random() < 0.08 else 0,
            "stage_label": "LIVE",
            "note": "",
            "weather": rng.choice(["Clear", "Cloudy", "Rain"]),
            "ground_condition": rng.choice(["Dry", "Damp", "Wet"]),
        }
        return reading
