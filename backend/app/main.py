from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import SessionLocal, init_db
from app.loader import load_csvs_into_db
from app.routers import (
    health,
    incidents,
    machines,
    operators,
    predictions,
    recommendations,
    safety,
    simulation,
    tasks,
    telemetry,
    training,
)
from app.ws import telemetry_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        load_csvs_into_db(db)
    finally:
        db.close()
    yield


app = FastAPI(title="CAT Operator Intelligence API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(machines.router)
app.include_router(operators.router)
app.include_router(tasks.router)
app.include_router(telemetry.router)
app.include_router(safety.router)
app.include_router(health.router)
app.include_router(predictions.router)
app.include_router(training.router)
app.include_router(incidents.router)
app.include_router(recommendations.router)
app.include_router(simulation.router)
app.include_router(telemetry_ws.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "cat-operator-intelligence-api"}
