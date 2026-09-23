"""Expert Moment Detector (spec sections 7, 30).

Gates when the system is allowed to speak up. An Expert Moment requires: a meaningful
situation, that it has persisted (not a single noisy tick), that reliable experience
exists for it, and that we are not re-announcing the same thing on every tick
(cooldown + duplicate suppression). This is what keeps the operator from being
interrupted constantly (spec section 30).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.expertise.situation import MEANINGFUL_SITUATIONS

DEFAULT_PERSISTENCE_TICKS = 2
DEFAULT_COOLDOWN_SECONDS = 25.0
HISTORY_WINDOW = 10


@dataclass
class MomentResult:
    triggered: bool
    reason: str


@dataclass
class ExpertMomentDetector:
    persistence_ticks: int = DEFAULT_PERSISTENCE_TICKS
    cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS
    _situation_history: dict[str, list[str]] = field(default_factory=dict)
    _last_trigger: dict[str, tuple[str, float]] = field(default_factory=dict)

    def evaluate(
        self,
        machine_id: str,
        situation_label: str,
        confidence_tier: str,
        pattern_key: str,
        now_ts: float | None = None,
    ) -> MomentResult:
        now_ts = now_ts if now_ts is not None else time.monotonic()

        history = self._situation_history.setdefault(machine_id, [])
        history.append(situation_label)
        self._situation_history[machine_id] = history[-HISTORY_WINDOW:]

        if situation_label not in MEANINGFUL_SITUATIONS:
            return MomentResult(False, "situation_normal")

        if confidence_tier == "none":
            return MomentResult(False, "no_reliable_experience")

        recent = self._situation_history[machine_id][-self.persistence_ticks :]
        persistent = len(recent) >= self.persistence_ticks and all(s == situation_label for s in recent)
        if not persistent:
            return MomentResult(False, "insufficient_persistence")

        last = self._last_trigger.get(machine_id)
        if last is not None:
            last_pattern, last_ts = last
            if last_pattern == pattern_key and (now_ts - last_ts) < self.cooldown_seconds:
                return MomentResult(False, "cooldown_duplicate_suppressed")

        self._last_trigger[machine_id] = (pattern_key, now_ts)
        return MomentResult(True, "expert_moment_detected")

    def reset(self, machine_id: str | None = None) -> None:
        if machine_id is None:
            self._situation_history.clear()
            self._last_trigger.clear()
        else:
            self._situation_history.pop(machine_id, None)
            self._last_trigger.pop(machine_id, None)
