"""Recommendation Confidence Engine (spec section 10).

Confidence is a weighted composite, not a single similarity score -- so a single
near-perfect match in an unmapped area, or many mediocre matches, both get treated more
cautiously than one strong, well-supported, well-grounded recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.expertise.matcher import ExperienceMatch
from app.expertise.situation import OperatingSituation

CONFIDENCE_WEIGHTS = {
    "similarity": 0.35,
    "historical_support": 0.15,
    "context_match": 0.15,
    "signal_quality": 0.15,
    "ground_confidence": 0.20,
}

CONFIDENCE_TIERS = {
    "high": 0.80,
    "low": 0.65,
}


@dataclass
class ConfidenceResult:
    score: float
    tier: str  # "high" | "low" | "none"
    components: dict[str, float]


def _historical_support(successful_count: int) -> float:
    return min(1.0, successful_count / 5.0)


def _context_match_fraction(matches: list[ExperienceMatch], situation: OperatingSituation) -> float:
    if not matches:
        return 0.0
    hits = sum(
        1
        for m in matches
        if m.episode.machine_model == situation.machine_model and m.episode.attachment == situation.attachment_type
    )
    return hits / len(matches)


def compute_confidence(
    matches: list[ExperienceMatch],
    situation: OperatingSituation,
    ground_confidence: float,
    signal_quality: float = 1.0,
) -> ConfidenceResult:
    successful = [m for m in matches if m.episode.outcome.get("successful", False)]

    if not successful:
        return ConfidenceResult(score=0.0, tier="none", components={})

    avg_similarity = sum(m.similarity for m in successful) / len(successful)
    historical_support = _historical_support(len(successful))
    context_match = _context_match_fraction(successful, situation)

    w = CONFIDENCE_WEIGHTS
    score = (
        w["similarity"] * avg_similarity
        + w["historical_support"] * historical_support
        + w["context_match"] * context_match
        + w["signal_quality"] * signal_quality
        + w["ground_confidence"] * ground_confidence
    )
    score = round(max(0.0, min(1.0, score)), 3)

    if score >= CONFIDENCE_TIERS["high"]:
        tier = "high"
    elif score >= CONFIDENCE_TIERS["low"]:
        tier = "low"
    else:
        tier = "none"

    return ConfidenceResult(
        score=score,
        tier=tier,
        components={
            "avg_similarity": round(avg_similarity, 3),
            "historical_support": round(historical_support, 3),
            "context_match": round(context_match, 3),
            "signal_quality": round(signal_quality, 3),
            "ground_confidence": round(ground_confidence, 3),
        },
    )
