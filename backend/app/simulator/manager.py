"""Process-wide simulation state: one simulator instance, started/stopped via REST,
streamed to any connected WebSocket clients via a broadcast queue per connection.
"""
from __future__ import annotations

import asyncio
from typing import Any

from app.simulator.telemetry_simulator import TelemetrySimulator


class SimulationManager:
    def __init__(self) -> None:
        self.simulator: TelemetrySimulator | None = None
        self.mode: str | None = None
        self.interval_seconds: float = 1.0
        self.running: bool = False
        self.ticks_emitted: int = 0
        self._task: asyncio.Task | None = None
        self._subscribers: list[asyncio.Queue] = []

    def status(self) -> dict[str, Any]:
        return {"running": self.running, "mode": self.mode, "ticks_emitted": self.ticks_emitted}

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    def start(self, mode: str = "scripted", interval_seconds: float = 1.0) -> None:
        if self.running:
            return
        self.simulator = TelemetrySimulator(mode=mode)
        self.mode = mode
        self.interval_seconds = interval_seconds
        self.running = True
        self.ticks_emitted = 0
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run_loop())

    def stop(self) -> None:
        self.running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _run_loop(self) -> None:
        assert self.simulator is not None
        try:
            while self.running:
                reading = self.simulator.next_reading()
                self.ticks_emitted += 1
                for q in list(self._subscribers):
                    if q.full():
                        try:
                            q.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                    await q.put(reading)
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            pass


simulation_manager = SimulationManager()
