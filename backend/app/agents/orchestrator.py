"""Orchestrator: combines Safety/Machine/Productivity/Training agent outputs and decides
what matters most to the operator right now (spec section 33)."""
from __future__ import annotations


def prioritize(safety: dict, machine: dict, productivity: dict) -> dict:
    """Ranks the three domains by how much attention they need (lower score = more urgent)."""
    domains = [
        {"domain": "safety", "score": safety["safety_score"], "reasons": safety["reasons"]},
        {"domain": "machine", "score": machine["machine_health_score"], "reasons": machine["reasons"]},
        {"domain": "productivity", "score": productivity["productivity_score"], "reasons": productivity["reasons"]},
    ]
    domains.sort(key=lambda d: d["score"])
    top = domains[0]

    return {
        "priority_domain": top["domain"],
        "priority_score": top["score"],
        "priority_reasons": top["reasons"],
        "ranked_domains": domains,
    }
