"""GET /recommendations/{machine_id} — Next Best Action.

Phase 2: placeholder "all normal" response. Phase 4/5 replace this with the real
Context Engine + Next Best Action Engine output (spec sections 16-18).
"""
from fastapi import APIRouter

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{machine_id}")
def get_recommendation(machine_id: str):
    return {
        "machine_id": machine_id,
        "risk_level": "Low",
        "next_best_action": None,
        "reason": "No elevated risk detected.",
        "note": "placeholder — Context Engine / NBA Engine not yet implemented (Phase 4-5)",
    }
