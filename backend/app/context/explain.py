"""Explainability layer (spec section 18): Detection -> Evidence -> Explanation -> Recommendation.

Deterministic, template-based text generation. No LLM dependency here -- this is the
fallback path that Phase 8's optional Ollama integration sits in front of, never behind
(spec section 36: the system must keep functioning without Ollama).
"""
from __future__ import annotations

_FACTOR_LABELS = {
    "cycle_time_deviation": "cycle time deviation from baseline",
    "idle_rate_deviation": "idle time above baseline",
    "proximity_events": "proximity event(s)",
    "seatbelt_violation": "a seatbelt violation",
    "hydraulic_temperature": "rising hydraulic temperature",
    "long_shift_duration": "extended shift duration",
    "wet_ground_condition": "wet ground conditions",
}


def _describe_factor(contributor: dict) -> str:
    label = _FACTOR_LABELS.get(contributor["factor"], contributor["factor"].replace("_", " "))
    value = contributor.get("value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if contributor["factor"] in ("cycle_time_deviation", "idle_rate_deviation"):
            return f"{label} of {round(value * 100)}%"
        return f"{label} ({value})"
    return label


def build_explanation(context: dict, nba: dict) -> dict:
    contributors = context["contributors"]

    if not contributors:
        detection = "No significant deviations detected."
        evidence = "All monitored signals are within normal range."
    else:
        top = contributors[:3]
        detection = f"Operational risk is {context['risk_trend'].lower()} ({context['risk_level'].lower()})."
        evidence = "Contributing factors: " + "; ".join(_describe_factor(c) for c in top) + "."

    explanation = (
        f"Current risk score is {context['risk_score']:.2f} ({context['risk_level']}), "
        f"driven primarily by {context.get('priority_domain', 'overall')} conditions."
    )

    recommendation = nba["action_label"]

    return {
        "detection": detection,
        "evidence": evidence,
        "explanation": explanation,
        "recommendation": recommendation,
        "priority": nba["priority"],
        "confidence": nba["confidence"],
        "source": "template",
    }


def format_as_text(explanation: dict) -> str:
    return (
        f"{explanation['detection']}\n\n"
        f"Reasons:\n- {explanation['evidence']}\n\n"
        f"Recommendation:\n{explanation['recommendation']}\n\n"
        f"Priority: {explanation['priority']}\n"
        f"Confidence: {round(explanation['confidence'] * 100)}%"
    )
