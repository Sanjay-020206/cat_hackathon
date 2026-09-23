import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.simulator.manager import simulation_manager

router = APIRouter()


@router.websocket("/ws/telemetry")
async def telemetry_ws(websocket: WebSocket):
    await websocket.accept()
    queue = simulation_manager.subscribe()
    try:
        while True:
            try:
                reading = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_json(reading)
            except asyncio.TimeoutError:
                # heartbeat/status even if simulation isn't running, so clients can
                # detect a live-but-idle connection vs. a dead one.
                await websocket.send_json({"type": "status", **simulation_manager.status()})
    except WebSocketDisconnect:
        pass
    finally:
        simulation_manager.unsubscribe(queue)
