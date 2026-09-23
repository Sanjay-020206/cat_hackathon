from fastapi import APIRouter

from app.schemas import SimulationStartRequest, SimulationStatus
from app.simulator.manager import simulation_manager

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/start", response_model=SimulationStatus)
async def start_simulation(req: SimulationStartRequest):
    simulation_manager.start(mode=req.mode, interval_seconds=req.interval_seconds)
    return simulation_manager.status()


@router.post("/stop", response_model=SimulationStatus)
async def stop_simulation():
    simulation_manager.stop()
    return simulation_manager.status()


@router.get("/status", response_model=SimulationStatus)
def simulation_status():
    return simulation_manager.status()
