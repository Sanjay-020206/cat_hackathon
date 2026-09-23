from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Machine(Base):
    __tablename__ = "machines"

    machine_id: Mapped[str] = mapped_column(String, primary_key=True)
    model: Mapped[str] = mapped_column(String)
    machine_type: Mapped[str] = mapped_column(String)
    age_years: Mapped[float] = mapped_column(Float)
    engine_hours: Mapped[float] = mapped_column(Float)
    maintenance_status: Mapped[str] = mapped_column(String)


class Operator(Base):
    __tablename__ = "operators"

    operator_id: Mapped[str] = mapped_column(String, primary_key=True)
    skill_level: Mapped[str] = mapped_column(String)
    experience_months: Mapped[int] = mapped_column(Integer)
    certifications: Mapped[str] = mapped_column(String)
    historical_cycle_time: Mapped[float] = mapped_column(Float)
    historical_idle_rate: Mapped[float] = mapped_column(Float)
    historical_safety_events: Mapped[float] = mapped_column(Float)


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[str] = mapped_column(String, index=True)
    machine_id: Mapped[str] = mapped_column(String, index=True)
    operator_id: Mapped[str] = mapped_column(String, index=True)
    engine_rpm: Mapped[int] = mapped_column(Integer)
    engine_temp: Mapped[float] = mapped_column(Float)
    hydraulic_pressure: Mapped[float] = mapped_column(Float)
    hydraulic_temp: Mapped[float] = mapped_column(Float)
    fuel_level: Mapped[float] = mapped_column(Float)
    fuel_rate: Mapped[float] = mapped_column(Float)
    engine_load: Mapped[float] = mapped_column(Float)
    speed: Mapped[float] = mapped_column(Float)
    cycle_time: Mapped[float] = mapped_column(Float)
    idle_time: Mapped[float] = mapped_column(Float)
    load_cycles: Mapped[int] = mapped_column(Integer)
    seatbelt_status: Mapped[str] = mapped_column(String)
    abnormal_scenario: Mapped[bool] = mapped_column(Boolean, default=False)


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(String, primary_key=True)
    machine_id: Mapped[str] = mapped_column(String, index=True)
    operator_id: Mapped[str] = mapped_column(String, index=True)
    task_type: Mapped[str] = mapped_column(String)
    material: Mapped[str] = mapped_column(String)
    target_quantity: Mapped[int] = mapped_column(Integer)
    deadline: Mapped[str] = mapped_column(String)
    zone: Mapped[str] = mapped_column(String)
    original_estimated_time: Mapped[float] = mapped_column(Float)


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[str] = mapped_column(String, index=True)
    machine_id: Mapped[str] = mapped_column(String, index=True)
    operator_id: Mapped[str] = mapped_column(String, index=True)
    event_type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    distance: Mapped[float] = mapped_column(Float)
    duration: Mapped[float] = mapped_column(Float)
    zone: Mapped[str] = mapped_column(String)


class Environment(Base):
    __tablename__ = "environment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[str] = mapped_column(String, index=True)
    site_id: Mapped[str] = mapped_column(String)
    weather: Mapped[str] = mapped_column(String)
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    visibility: Mapped[float] = mapped_column(Float)
    rainfall: Mapped[float] = mapped_column(Float)
    terrain: Mapped[str] = mapped_column(String)
    ground_condition: Mapped[str] = mapped_column(String)
    dust_level: Mapped[float] = mapped_column(Float)


class TaskHistory(Base):
    __tablename__ = "task_history"

    task_id: Mapped[str] = mapped_column(String, primary_key=True)
    task_type: Mapped[str] = mapped_column(String)
    weather: Mapped[str] = mapped_column(String)
    operator_skill: Mapped[str] = mapped_column(String)
    machine_age: Mapped[float] = mapped_column(Float)
    terrain: Mapped[str] = mapped_column(String)
    load: Mapped[float] = mapped_column(Float)
    historical_cycle_time: Mapped[float] = mapped_column(Float)
    estimated_time: Mapped[float] = mapped_column(Float)
    actual_time: Mapped[float] = mapped_column(Float)


class Training(Base):
    __tablename__ = "training"

    training_id: Mapped[str] = mapped_column(String, primary_key=True)
    skill: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    duration: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[str] = mapped_column(String)
    resource: Mapped[str] = mapped_column(String)


class Incident(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[str] = mapped_column(String, index=True)
    machine_id: Mapped[str] = mapped_column(String, index=True)
    operator_id: Mapped[str] = mapped_column(String, index=True)
    site_zone: Mapped[str] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    trigger: Mapped[str] = mapped_column(String)
    action_taken: Mapped[str] = mapped_column(String)
    outcome: Mapped[str] = mapped_column(String)
