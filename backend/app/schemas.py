from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MachineOut(ORMModel):
    machine_id: str
    model: str
    machine_type: str
    age_years: float
    engine_hours: float
    maintenance_status: str


class OperatorOut(ORMModel):
    operator_id: str
    skill_level: str
    experience_months: int
    certifications: str
    historical_cycle_time: float
    historical_idle_rate: float
    historical_safety_events: float


class TelemetryOut(ORMModel):
    id: int
    timestamp: str
    machine_id: str
    operator_id: str
    engine_rpm: int
    engine_temp: float
    hydraulic_pressure: float
    hydraulic_temp: float
    fuel_level: float
    fuel_rate: float
    engine_load: float
    speed: float
    cycle_time: float
    idle_time: float
    load_cycles: int
    seatbelt_status: str
    abnormal_scenario: bool


class TaskOut(ORMModel):
    task_id: str
    machine_id: str
    operator_id: str
    task_type: str
    material: str
    target_quantity: int
    deadline: str
    zone: str
    original_estimated_time: float


class SafetyEventOut(ORMModel):
    event_id: str
    timestamp: str
    machine_id: str
    operator_id: str
    event_type: str
    severity: str
    distance: float
    duration: float
    zone: str


class EnvironmentOut(ORMModel):
    id: int
    timestamp: str
    site_id: str
    weather: str
    temperature: float
    humidity: float
    visibility: float
    rainfall: float
    terrain: str
    ground_condition: str
    dust_level: float


class TrainingOut(ORMModel):
    training_id: str
    skill: str
    title: str
    duration: int
    difficulty: str
    resource: str


class IncidentIn(BaseModel):
    incident_id: str
    timestamp: str
    machine_id: str
    operator_id: str
    site_zone: str
    event_type: str
    severity: str
    trigger: str
    action_taken: str
    outcome: str


class IncidentOut(ORMModel, IncidentIn):
    pass


class SimulationStartRequest(BaseModel):
    mode: str = "scripted"  # "scripted" | "random"
    interval_seconds: float = 1.0


class SimulationStatus(BaseModel):
    running: bool
    mode: str | None = None
    ticks_emitted: int = 0
