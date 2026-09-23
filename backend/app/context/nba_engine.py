"""Next Best Action Engine (spec section 17).

Takes the fused context (+ risk trajectory) and produces a human-readable, actionable
recommendation: {action, reason, priority, confidence}.
"""
from __future__ import annotations

# Ordered rules: first matching rule wins. Each rule inspects the fused context dict and,
# if triggered, returns (action_key, action_label, priority, base_confidence).
_RULES: list[tuple[str, str, str, float]] = []


def _reposition_rule(context: dict) -> tuple[str, str, str, float] | None:
    factors = {c["factor"] for c in context["contributors"]}
    if (
        context["risk_level"] in ("Elevated", "High")
        and "proximity_events" in factors
        and ("cycle_time_deviation" in factors or "hydraulic_temperature" in factors)
    ):
        return (
            "reposition_before_continuing",
            "Reposition before continuing excavation.",
            "High",
            0.84,
        )
    return None


def _seatbelt_rule(context: dict) -> tuple[str, str, str, float] | None:
    factors = {c["factor"] for c in context["contributors"]}
    if "seatbelt_violation" in factors:
        return (
            "fasten_seatbelt_and_pause",
            "Fasten seatbelt and pause operation until confirmed.",
            "High",
            0.95,
        )
    return None


def _reduce_speed_rule(context: dict) -> tuple[str, str, str, float] | None:
    factors = {c["factor"] for c in context["contributors"]}
    if "proximity_events" in factors and context["risk_level"] != "Low":
        return (
            "reduce_speed_and_reassess_zone",
            "Reduce speed and reassess the operating zone.",
            "High",
            0.8,
        )
    return None


def _machine_watch_rule(context: dict) -> tuple[str, str, str, float] | None:
    factors = {c["factor"] for c in context["contributors"]}
    if "hydraulic_temperature" in factors and context["risk_level"] in ("Moderate", "Elevated"):
        return (
            "monitor_hydraulic_temperature",
            "Monitor hydraulic temperature; schedule a maintenance check if it continues to rise.",
            "Medium",
            0.7,
        )
    return None


def _idle_reduction_rule(context: dict) -> tuple[str, str, str, float] | None:
    factors = {c["factor"] for c in context["contributors"]}
    if "idle_rate_deviation" in factors and context["risk_level"] != "Low":
        return (
            "reduce_idle_time",
            "Reduce idle time between load cycles to stay on pace.",
            "Medium",
            0.65,
        )
    return None


def _continue_normally(context: dict) -> tuple[str, str, str, float]:
    return ("continue_operation", "Continue current operation; conditions are within normal range.", "Low", 0.9)


_RULE_FUNCS = [
    _seatbelt_rule,
    _reposition_rule,
    _reduce_speed_rule,
    _machine_watch_rule,
    _idle_reduction_rule,
]


def next_best_action(context: dict) -> dict:
    for rule in _RULE_FUNCS:
        result = rule(context)
        if result is not None:
            action_key, action_label, priority, base_confidence = result
            # confidence nudged by how many corroborating contributors exist
            confidence = min(0.97, base_confidence + 0.02 * max(0, len(context["contributors"]) - 1))
            return {
                "action": action_key,
                "action_label": action_label,
                "priority": priority,
                "confidence": round(confidence, 2),
            }

    action_key, action_label, priority, base_confidence = _continue_normally(context)
    return {"action": action_key, "action_label": action_label, "priority": priority, "confidence": base_confidence}
