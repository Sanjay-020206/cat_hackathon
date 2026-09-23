"""Expert Episode Memory (spec sections 8, 28-29).

`ExpertEpisode` represents a stored operating experience -- successful or not -- that the
Experience Matcher can retrieve against. All episodes here are **synthetic demo data**,
clearly labeled as such; a production system would populate this from real operator
sessions.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.expertise.situation import MACHINE_TYPE_TO_ATTACHMENT

SEED = 11

ACTION_LIBRARY = {
    "HIGH_RESISTANCE_DIGGING": [
        ["reduce_penetration", "reposition_bucket", "apply_breakout", "lift", "reposition"],
        ["reposition_bucket", "apply_breakout", "lift"],
        ["reduce_penetration", "reposition_bucket", "apply_breakout"],
    ],
    "LOW_PENETRATION": [
        ["increase_boom_angle", "reduce_penetration", "reposition"],
        ["reposition", "reduce_penetration"],
    ],
    "EXCESSIVE_HYDRAULIC_LOAD": [
        ["reduce_penetration", "slow_approach", "reposition"],
        ["slow_approach", "reposition_bucket"],
    ],
    "UNSTABLE_OPERATION": [
        ["slow_approach", "reposition", "reduce_penetration"],
        ["reposition", "slow_approach"],
    ],
    "INEFFICIENT_CYCLE": [
        ["reposition_bucket", "slow_approach"],
        ["reduce_penetration", "reposition_bucket"],
    ],
    "UNUSUAL_MATERIAL_RESPONSE": [
        ["slow_approach", "reduce_penetration", "reposition_bucket", "apply_breakout"],
        ["reposition", "reduce_penetration"],
    ],
}

# Cells (from app.site.grid's deterministic hotspots) that get a concentration of episodes,
# so the "ground + expert experience combination" (spec section 24) has something to find
# near the areas the demo machine actually travels through.
_EPISODE_CELL_POOL = ["D4", "E4", "F4", "F3", "G3", "G2", "G4", "F2"]


@dataclass
class ExpertEpisode:
    episode_id: str
    machine_model: str
    attachment: str
    task: str
    situation: str

    context: dict[str, float]
    operator_profile: dict[str, str]
    action_sequence: list[str]
    outcome: dict[str, float | bool]

    cell_id: str | None = None
    quality_score: float = 0.0
    is_synthetic: bool = True


def experience_quality_score(episode: ExpertEpisode) -> float:
    """ExperienceQualityScore (spec section 28): only sufficiently good episodes should
    enter the trusted pool used for recommendations."""
    outcome = episode.outcome
    if not outcome.get("successful", False):
        return 0.0

    # Efficiency: lower energy/cycle relative to the situation's typical range is better.
    efficiency = max(0.0, min(1.0, 1.0 - (float(outcome.get("energy_per_cycle", 1.0)) - 0.4) / 1.2))
    # Stability: inferred from vibration recorded in context (lower is better).
    stability = max(0.0, 1.0 - float(episode.context.get("vibration", 0.3)))
    # Signal quality: proxy for how complete the recorded context is.
    signal_quality = 1.0 if len(episode.context) >= 4 else 0.6
    experience_bonus = 0.1 if episode.operator_profile.get("experience_level") == "expert" else 0.0

    score = 0.4 * efficiency + 0.25 * stability + 0.2 * signal_quality + 0.15 + experience_bonus
    return round(max(0.0, min(1.0, score)), 3)


def generate_synthetic_episodes(seed: int = SEED, count: int = 48) -> list[ExpertEpisode]:
    rng = random.Random(seed)
    situations = list(ACTION_LIBRARY.keys())
    episodes: list[ExpertEpisode] = []

    for i in range(count):
        situation = rng.choices(situations, weights=[40, 15, 12, 10, 13, 10])[0]
        sequences = ACTION_LIBRARY[situation]
        action_sequence = rng.choice(sequences)

        machine_model = rng.choice(["CAT 320", "CAT 336", "CAT 950", "CAT 966"])
        machine_type = "Wheel Loader" if machine_model in ("CAT 950", "CAT 966") else "Excavator"
        attachment = MACHINE_TYPE_TO_ATTACHMENT[machine_type]

        experience_level = rng.choices(["expert", "intermediate", "novice"], weights=[55, 30, 15])[0]
        # Experts succeed far more often; this is what makes their episodes worth retrieving.
        base_success_rate = {"expert": 0.88, "intermediate": 0.55, "novice": 0.30}[experience_level]
        successful = rng.random() < base_success_rate

        resistance = rng.uniform(0.55, 0.95) if situation != "LOW_PENETRATION" else rng.uniform(0.2, 0.5)
        hydraulic_pressure = round(20 + resistance * 15 + rng.uniform(-2, 2), 1)
        penetration = round(max(0.05, 1.0 - resistance * 0.8 + rng.uniform(-0.05, 0.05)), 3)
        engine_load = round(45 + resistance * 40 + rng.uniform(-5, 5), 1)
        vibration = round(max(0.0, min(1.0, 0.5 * resistance + rng.uniform(-0.1, 0.15))), 3)

        base_cycle = 44.0 * (1 + resistance * 0.6)
        cycle_time = round(base_cycle * (0.85 if successful and experience_level == "expert" else 1.05), 1)
        energy_per_cycle = round(0.4 + resistance * 0.8 + (0 if successful else 0.15), 3)

        cell_id = rng.choice(_EPISODE_CELL_POOL) if situation == "HIGH_RESISTANCE_DIGGING" else None

        episode = ExpertEpisode(
            episode_id=f"EP-{i + 1:03d}",
            machine_model=machine_model,
            attachment=attachment,
            task="digging",
            situation=situation,
            context={
                "material_resistance": round(resistance, 3),
                "hydraulic_pressure": hydraulic_pressure,
                "penetration_rate": penetration,
                "engine_load": engine_load,
                "vibration": vibration,
            },
            operator_profile={"experience_level": experience_level},
            action_sequence=action_sequence,
            outcome={
                "cycle_time": cycle_time,
                "energy_per_cycle": energy_per_cycle,
                "successful": successful,
            },
            cell_id=cell_id,
        )
        episode.quality_score = experience_quality_score(episode)
        episodes.append(episode)

    return episodes
