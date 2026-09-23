"""Experience Similarity Engine (spec section 9).

Given the current operating situation (+ current ground condition, spec section 24),
retrieves the top-K most similar trusted expert episodes. Plain cosine similarity over a
normalized feature vector + a handful of context bonuses -- no vector database needed at
this dataset size (spec section 9: "do not introduce unnecessary infrastructure").
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from app.expertise.episodes import ExpertEpisode
from app.expertise.situation import OperatingSituation

FEATURE_KEYS = ["material_resistance", "penetration_rate", "hydraulic_pressure", "engine_load", "vibration"]
_NORMALIZERS = {"hydraulic_pressure": 40.0, "engine_load": 100.0}


@dataclass
class ExperienceMatch:
    episode: ExpertEpisode
    similarity: float


def _situation_vector(situation: OperatingSituation) -> list[float]:
    raw = {
        "material_resistance": situation.material_resistance,
        "penetration_rate": situation.penetration_rate,
        "hydraulic_pressure": situation.hydraulic_pressure,
        "engine_load": situation.engine_load,
        "vibration": situation.vibration_level,
    }
    return [raw[k] / _NORMALIZERS.get(k, 1.0) for k in FEATURE_KEYS]


def _episode_vector(episode: ExpertEpisode) -> list[float]:
    ctx = episode.context
    return [ctx.get(k, 0.0) / _NORMALIZERS.get(k, 1.0) for k in FEATURE_KEYS]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class ExperienceMatcher:
    def __init__(self, episodes: list[ExpertEpisode], min_quality: float = 0.45) -> None:
        self.trusted_episodes = [e for e in episodes if e.quality_score >= min_quality]
        self.all_episodes = episodes

    def find_similar(
        self,
        situation: OperatingSituation,
        situation_label: str,
        top_k: int = 5,
        cell_id: str | None = None,
        include_untrusted: bool = False,
    ) -> list[ExperienceMatch]:
        pool = self.all_episodes if include_untrusted else self.trusted_episodes
        # Hard filter: same task and same situation bucket -- retrieving a "digging"
        # episode for a "digging" situation only (spec section 9's context match).
        candidates = [e for e in pool if e.task == "digging" and e.situation == situation_label]

        query_vec = _situation_vector(situation)
        scored: list[ExperienceMatch] = []
        for episode in candidates:
            similarity = _cosine_similarity(query_vec, _episode_vector(episode))

            if episode.machine_model == situation.machine_model:
                similarity += 0.03
            if episode.attachment == situation.attachment_type:
                similarity += 0.02
            if cell_id is not None and episode.cell_id == cell_id:
                similarity += 0.05

            similarity = max(0.0, min(1.0, similarity))
            scored.append(ExperienceMatch(episode=episode, similarity=round(similarity, 3)))

        scored.sort(key=lambda m: -m.similarity)
        return scored[:top_k]
