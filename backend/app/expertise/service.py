"""ExpertiseEngine: orchestrates the full CAT Expertise Engine pipeline (spec section 46):

    telemetry -> situation recognition -> area lookup -> ground/energy intelligence
    -> expert moment detection -> experience retrieval -> confidence -> expert pattern
    -> energy-aware Next Best Action -> (later) outcome -> learning loop

This sits alongside the existing Context Engine / NBA Engine (app/context/*) rather than
replacing it -- the two answer different questions ("is this operationally risky right
now?" vs. "have experts handled *this exact kind of situation* successfully before, and
what did they do?").

All demo data (episodes, jobsite grid) is synthetic and explicitly labeled as such in
every response (`"data_source": "synthetic_demo"`) -- see CAT_Expertise_Engine_Claude_Code_Prompt.md
section 18 and 34.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from app.expertise.confidence import compute_confidence
from app.expertise.demo_path import cell_id_for_tick, position_for_tick
from app.expertise.energy import estimate_energy_per_cycle
from app.expertise.episodes import ExpertEpisode, experience_quality_score, generate_synthetic_episodes
from app.expertise.matcher import ExperienceMatcher
from app.expertise.moment_detector import ExpertMomentDetector
from app.expertise.pattern import extract_expert_pattern
from app.expertise.situation import MEANINGFUL_SITUATIONS, classify_situation, derive_operating_situation
from app.site.energy_forecast import forecast_area_energy
from app.site.ground import GroundObservation, get_ground_estimate, update_cell_from_observation
from app.site.grid import generate_site_grid

TRUSTED_QUALITY_THRESHOLD = 0.45


class ExpertiseEngine:
    def __init__(self) -> None:
        self.site_cells = generate_site_grid()
        self.episodes: list[ExpertEpisode] = generate_synthetic_episodes()
        self.matcher = ExperienceMatcher(self.episodes, min_quality=TRUSTED_QUALITY_THRESHOLD)
        self.moment_detector = ExpertMomentDetector()

        self._tick_counts: dict[str, int] = {}
        self._previous_readings: dict[str, dict] = {}
        self._last_context: dict[str, dict] = {}
        self._new_episodes_today = 0

    def evaluate(
        self,
        reading: dict,
        machine_model: str,
        machine_type: str,
        task_type: str = "Earth Excavation",
        operator_skill: str = "Intermediate",
    ) -> dict:
        machine_id = reading["machine_id"]
        tick = self._tick_counts.get(machine_id, 0) + 1
        self._tick_counts[machine_id] = tick

        stage_index = reading.get("stage_index")
        x, y, depth = position_for_tick(stage_index, tick)
        cell_id = cell_id_for_tick(stage_index, tick)
        cell = self.site_cells[cell_id]

        previous_reading = self._previous_readings.get(machine_id)
        situation = derive_operating_situation(
            reading,
            machine_model=machine_model,
            machine_type=machine_type,
            task_type=task_type,
            operator_skill=operator_skill,
            previous_reading=previous_reading,
            position=(x, y, depth),
        )
        self._previous_readings[machine_id] = reading

        situation_label = classify_situation(situation)
        ground_estimate = get_ground_estimate(cell)
        energy_forecast = forecast_area_energy(cell)

        matches = self.matcher.find_similar(situation, situation_label, top_k=5, cell_id=cell_id)
        pattern = extract_expert_pattern(matches)
        confidence = compute_confidence(matches, situation, ground_confidence=cell.material_confidence)

        pattern_key = "|".join(pattern["pattern"]) if pattern else "none"
        moment = self.moment_detector.evaluate(machine_id, situation_label, confidence.tier, pattern_key)

        next_best_action = None
        expert_moment: dict = {"triggered": False, "situation": situation_label, "reason": moment.reason}

        if moment.triggered and pattern is not None:
            next_best_action = {
                "action_sequence": pattern["pattern"],
                "reason": (
                    f"{pattern['supporting_episode_count']} similar successful episode(s) "
                    f"in comparable ground conditions."
                ),
                "confidence": confidence.score,
                "priority": "high" if confidence.tier == "high" else "medium",
            }
            expert_moment = {"triggered": True, "situation": situation_label, "reason": "expert_moment_detected"}
        elif situation_label in MEANINGFUL_SITUATIONS and confidence.tier == "none":
            expert_moment = {
                "triggered": False,
                "situation": situation_label,
                "reason": "NO_RELIABLE_EXPERIENCE_FOUND",
            }

        top_matches_summary = [
            {
                "episode_id": m.episode.episode_id,
                "similarity": m.similarity,
                "action_sequence": m.episode.action_sequence,
                "successful": m.episode.outcome.get("successful", False),
                "cycle_time": m.episode.outcome.get("cycle_time"),
                "energy_per_cycle": m.episode.outcome.get("energy_per_cycle"),
                "operator_experience_level": m.episode.operator_profile.get("experience_level"),
            }
            for m in matches
        ]

        self._last_context[machine_id] = {
            "situation": situation_label,
            "situation_obj": situation,
            "cell_id": cell_id,
            "pattern": pattern,
            "machine_model": machine_model,
            "attachment": situation.attachment_type,
        }

        return {
            "machine_id": machine_id,
            "situation": situation_label,
            "operating_situation": asdict(situation),
            "area": {"cell_id": cell_id, "x": x, "y": y, "depth": depth},
            "ground_estimate": ground_estimate,
            "energy_forecast": energy_forecast,
            "expert_moment": expert_moment,
            "matches": top_matches_summary,
            "pattern": pattern,
            "confidence": {
                "score": confidence.score,
                "tier": confidence.tier,
                "components": confidence.components,
            },
            "next_best_action": next_best_action,
            "data_source": "synthetic_demo",
        }

    def record_outcome(self, machine_id: str, cycle_time_after: float, successful: bool) -> dict:
        last = self._last_context.get(machine_id)
        if last is None:
            raise ValueError(f"No prior expertise evaluation found for machine {machine_id}")

        situation = last["situation_obj"]
        cell_id = last["cell_id"]
        cell = self.site_cells[cell_id]
        confidence_before = cell.material_confidence

        obs = GroundObservation(
            cell_id=cell_id,
            hydraulic_pressure=situation.hydraulic_pressure,
            engine_load=situation.engine_load,
            cycle_time=cycle_time_after,
            material_resistance=situation.material_resistance,
            successful=successful,
        )
        update_cell_from_observation(cell, obs)

        new_episode_id = None
        if successful:
            pattern = last.get("pattern")
            action_sequence = pattern["pattern"] if pattern else ["reposition"]
            energy = estimate_energy_per_cycle(
                situation.hydraulic_pressure, cycle_time_after, situation.material_resistance, situation.engine_load
            )
            episode = ExpertEpisode(
                episode_id=f"EP-LEARN-{len(self.episodes) + 1:03d}",
                machine_model=last["machine_model"],
                attachment=last["attachment"],
                task="digging",
                situation=last["situation"],
                context={
                    "material_resistance": situation.material_resistance,
                    "hydraulic_pressure": situation.hydraulic_pressure,
                    "penetration_rate": situation.penetration_rate,
                    "engine_load": situation.engine_load,
                    "vibration": situation.vibration_level,
                },
                operator_profile={"experience_level": situation.operator_experience_level},
                action_sequence=action_sequence,
                outcome={"cycle_time": cycle_time_after, "energy_per_cycle": energy, "successful": True},
                cell_id=cell_id,
                is_synthetic=False,
            )
            episode.quality_score = experience_quality_score(episode)
            if episode.quality_score >= TRUSTED_QUALITY_THRESHOLD:
                self.episodes.append(episode)
                self.matcher.trusted_episodes.append(episode)
                self._new_episodes_today += 1
                new_episode_id = episode.episode_id

        return {
            "cell_id": cell_id,
            "material_confidence_before": confidence_before,
            "material_confidence_after": cell.material_confidence,
            "observation_count": cell.observation_count,
            "new_episode_stored": new_episode_id is not None,
            "episode_id": new_episode_id,
            "updated_at": cell.last_updated,
        }

    def statistics(self) -> dict:
        cells = list(self.site_cells.values())
        mapped = [c for c in cells if c.observation_count > 0]
        high_resistance = [c for c in mapped if c.excavation_difficulty == "HIGH"]
        low_resistance = [c for c in mapped if c.excavation_difficulty == "LOW"]
        unknown = [c for c in cells if c.observation_count == 0]
        trusted_patterns = len(self.matcher.trusted_episodes)

        return {
            "areas_mapped": len(mapped),
            "total_areas": len(cells),
            "known_high_resistance_areas": len(high_resistance),
            "known_low_resistance_areas": len(low_resistance),
            "unknown_areas": len(unknown),
            "successful_patterns": trusted_patterns,
            "new_patterns_learned_today": self._new_episodes_today,
            "as_of": datetime.now(timezone.utc).isoformat(),
            "data_source": "synthetic_demo",
        }

    def machine_memory(self) -> dict:
        by_situation: dict[str, int] = {}
        for e in self.episodes:
            by_situation[e.situation] = by_situation.get(e.situation, 0) + 1

        return {
            "total_episodes": len(self.episodes),
            "trusted_episodes": len(self.matcher.trusted_episodes),
            "episodes_by_situation": by_situation,
            "new_episodes_this_session": self._new_episodes_today,
            "data_source": "synthetic_demo",
        }

    def reset(self, machine_id: str | None = None) -> None:
        if machine_id is None:
            self._tick_counts.clear()
            self._previous_readings.clear()
            self._last_context.clear()
        else:
            self._tick_counts.pop(machine_id, None)
            self._previous_readings.pop(machine_id, None)
            self._last_context.pop(machine_id, None)
        self.moment_detector.reset(machine_id)


_engine: ExpertiseEngine | None = None


def get_expertise_engine() -> ExpertiseEngine:
    global _engine
    if _engine is None:
        _engine = ExpertiseEngine()
    return _engine


def reset_expertise_engine() -> None:
    """Test hook: forces a fresh engine (new grid + episodes + cleared memory) on next
    get_expertise_engine() call."""
    global _engine
    _engine = None
