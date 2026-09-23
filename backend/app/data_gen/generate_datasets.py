"""
Synthetic dataset generator for CAT Operator Intelligence.

Builds the logical datasets defined in the spec (machines, operators, telemetry, tasks,
safety_events, environment, task_history, training) with causal relationships instead of
independent random noise:

  Weather:        rain -> terrain difficulty up -> cycle time up -> fuel up -> task duration up
  Long shift:     shift length up -> fatigue proxy up -> behavior deviation up -> safety events up
  Heavy load:     load up -> hydraulic load up -> fuel rate up -> temperature up
  Machine age:    age up -> efficiency down slightly -> maintenance risk up slightly
  Operator skill: skill up -> cycle time down -> idle down -> productivity up

Scenarios are ~80-90% normal, ~10-20% abnormal (seatbelt violation, overspeed, proximity events,
excessive idle, fuel anomaly, hydraulic temp trend, heavy load, wet terrain, task delay, and a
"combined deterioration" scenario used as the primary demo).

Run directly to (re)generate all CSVs under backend/data/.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SEED = 42
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)

MACHINE_MODELS = ["CAT 320", "CAT 336", "CAT 950", "CAT 966", "CAT D6"]
MACHINE_TYPES = ["Excavator", "Excavator", "Wheel Loader", "Wheel Loader", "Dozer"]
TASK_TYPES = ["Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"]
WEATHERS = ["Clear", "Cloudy", "Rain", "Heavy Rain"]
TERRAINS = ["Flat", "Uneven", "Rocky", "Muddy"]
GROUND_CONDITIONS = ["Dry", "Damp", "Wet", "Waterlogged"]
SKILL_LEVELS = ["Novice", "Intermediate", "Skilled", "Expert"]
CERTIFICATIONS = ["Basic Ops", "Advanced Ops", "Safety Cert", "Heavy Load Cert"]
MATERIALS = ["Soil", "Rock", "Gravel", "Debris", "Concrete"]
ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"]

N_MACHINES = 10
N_OPERATORS = 15
N_TASKS = 60
N_TELEMETRY_PER_TASK = 40  # ~ rows of telemetry sampled during a task
N_SAFETY_EVENTS = 90
N_ENV_ROWS = 120
N_TASK_HISTORY = 400

ABNORMAL_RATE = 0.15  # 15% abnormal overall, within the 10-20% band from the spec


def _rng() -> np.random.Generator:
    return np.random.default_rng(SEED)


def gen_machines(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for i in range(N_MACHINES):
        idx = i % len(MACHINE_MODELS)
        age = round(rng.uniform(0.5, 12.0), 1)
        engine_hours = round(age * rng.uniform(700, 1400), 1)
        # Relationship 4: machine age up -> maintenance risk slightly up
        maintenance_risk = min(0.95, 0.05 + age * 0.045 + rng.normal(0, 0.03))
        maintenance_status = (
            "Critical" if maintenance_risk > 0.7 else "Watch" if maintenance_risk > 0.4 else "Normal"
        )
        rows.append(
            {
                "machine_id": f"EXC{i+1:03d}" if MACHINE_TYPES[idx] == "Excavator" else f"MCH{i+1:03d}",
                "model": MACHINE_MODELS[idx],
                "machine_type": MACHINE_TYPES[idx],
                "age_years": age,
                "engine_hours": engine_hours,
                "maintenance_status": maintenance_status,
            }
        )
    return pd.DataFrame(rows)


def gen_operators(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for i in range(N_OPERATORS):
        skill = rng.choice(SKILL_LEVELS, p=[0.2, 0.35, 0.3, 0.15])
        skill_idx = SKILL_LEVELS.index(skill)
        experience_months = int(rng.uniform(2, 15) * (skill_idx + 1))
        # Relationship 5: skill up -> cycle time down, idle down
        base_cycle = 60 - skill_idx * 6 + rng.normal(0, 3)
        base_idle = 18 - skill_idx * 3 + rng.normal(0, 2)
        base_safety = max(0.0, 1.2 - skill_idx * 0.3 + rng.normal(0, 0.15))
        n_certs = rng.integers(1, 3)
        certs = ",".join(rng.choice(CERTIFICATIONS, size=n_certs, replace=False))
        rows.append(
            {
                "operator_id": f"OP{1001 + i}",
                "skill_level": skill,
                "experience_months": experience_months,
                "certifications": certs,
                "historical_cycle_time": round(max(30, base_cycle), 1),
                "historical_idle_rate": round(max(3, base_idle), 1),
                "historical_safety_events": round(max(0, base_safety), 2),
            }
        )
    return pd.DataFrame(rows)


def gen_environment(rng: np.random.Generator, site_ids: list[str]) -> pd.DataFrame:
    rows = []
    start = datetime(2026, 9, 1, 6, 0, 0)
    for i in range(N_ENV_ROWS):
        ts = start + timedelta(minutes=15 * i)
        weather = rng.choice(WEATHERS, p=[0.55, 0.2, 0.18, 0.07])
        is_rain = weather in ("Rain", "Heavy Rain")
        rainfall = round(rng.uniform(2, 15) if is_rain else rng.uniform(0, 0.5), 2)
        # Relationship 1: rain -> terrain difficulty up -> muddier/wetter ground
        terrain = rng.choice(TERRAINS, p=[0.15, 0.15, 0.1, 0.6] if is_rain else [0.5, 0.3, 0.15, 0.05])
        ground_condition = rng.choice(
            GROUND_CONDITIONS, p=[0.05, 0.15, 0.35, 0.45] if is_rain else [0.6, 0.25, 0.1, 0.05]
        )
        rows.append(
            {
                "timestamp": ts.isoformat(),
                "site_id": rng.choice(site_ids),
                "weather": weather,
                "temperature": round(rng.uniform(18, 26) if is_rain else rng.uniform(22, 38), 1),
                "humidity": round(rng.uniform(70, 95) if is_rain else rng.uniform(30, 65), 1),
                "visibility": round(rng.uniform(2, 6) if is_rain else rng.uniform(7, 10), 1),
                "rainfall": rainfall,
                "terrain": terrain,
                "ground_condition": ground_condition,
                "dust_level": round(rng.uniform(0, 15) if is_rain else rng.uniform(10, 60), 1),
            }
        )
    return pd.DataFrame(rows)


def gen_tasks(rng: np.random.Generator, machines: pd.DataFrame, operators: pd.DataFrame) -> pd.DataFrame:
    rows = []
    start = datetime(2026, 9, 22, 7, 0, 0)
    for i in range(N_TASKS):
        machine = machines.sample(random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        operator = operators.sample(random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        task_type = rng.choice(TASK_TYPES)
        target_qty = int(rng.uniform(80, 300))
        est_time = round(target_qty * rng.uniform(0.9, 1.3), 1)
        deadline = start + timedelta(hours=int(rng.uniform(2, 10)), minutes=int(rng.uniform(0, 59)))
        rows.append(
            {
                "task_id": f"TASK{i+1:04d}",
                "machine_id": machine["machine_id"],
                "operator_id": operator["operator_id"],
                "task_type": task_type,
                "material": rng.choice(MATERIALS),
                "target_quantity": target_qty,
                "deadline": deadline.isoformat(),
                "zone": rng.choice(ZONES),
                "original_estimated_time": est_time,
            }
        )
        start += timedelta(minutes=int(rng.uniform(20, 90)))
    return pd.DataFrame(rows)


def _abnormal_flags(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.random(n) < ABNORMAL_RATE


def gen_telemetry(
    rng: np.random.Generator, tasks: pd.DataFrame, machines: pd.DataFrame, operators: pd.DataFrame, env: pd.DataFrame
) -> pd.DataFrame:
    machines_idx = machines.set_index("machine_id")
    operators_idx = operators.set_index("operator_id")
    rows = []

    for _, task in tasks.iterrows():
        machine = machines_idx.loc[task["machine_id"]]
        operator = operators_idx.loc[task["operator_id"]]
        env_row = env.sample(random_state=int(rng.integers(0, 1_000_000))).iloc[0]

        is_rain = env_row["weather"] in ("Rain", "Heavy Rain")
        terrain_penalty = {"Flat": 0, "Uneven": 4, "Rocky": 7, "Muddy": 10}[env_row["terrain"]]
        skill_idx = SKILL_LEVELS.index(operator["skill_level"])
        age_penalty = machine["age_years"] * 0.4  # Relationship 4: age -> efficiency down slightly

        shift_start = datetime.fromisoformat(task["deadline"]) - timedelta(hours=6)
        abnormal_task = rng.random() < ABNORMAL_RATE

        for t in range(N_TELEMETRY_PER_TASK):
            ts = shift_start + timedelta(minutes=8 * t)
            shift_minutes = t * 8
            # Relationship 2: long shift -> fatigue proxy up -> behavior deviation up
            fatigue = min(1.0, shift_minutes / (5 * 60))

            load_cycles = int(rng.integers(3, 12))
            # Relationship 3: load up -> hydraulic load up -> fuel rate up -> temp up
            load_factor = load_cycles / 12.0

            base_cycle = operator["historical_cycle_time"]
            cycle_time = (
                base_cycle
                + terrain_penalty
                + age_penalty
                + fatigue * 8
                + rng.normal(0, 3)
            )
            idle_time = max(0.0, operator["historical_idle_rate"] * 0.6 + fatigue * 6 + rng.normal(0, 2))

            engine_load = min(100.0, 45 + load_factor * 35 + rng.normal(0, 5))
            hydraulic_pressure = 20 + load_factor * 12 + rng.normal(0, 1.5)
            hydraulic_temp = 55 + load_factor * 20 + fatigue * 5 + rng.normal(0, 2)
            fuel_rate = 3.5 + load_factor * 4 + (2 if is_rain else 0) + rng.normal(0, 0.4)
            fuel_level = max(5.0, 90 - shift_minutes * 0.08 - fuel_rate * 0.5)
            engine_rpm = int(1400 + load_factor * 500 + rng.normal(0, 40))
            engine_temp = 75 + load_factor * 10 + rng.normal(0, 2)
            speed = max(0.5, 4.5 - terrain_penalty * 0.15 + rng.normal(0, 0.4))

            seatbelt = "Fastened"
            if abnormal_task and rng.random() < 0.2:
                seatbelt = "Unfastened"

            if abnormal_task:
                variant = rng.integers(0, 7)
                if variant == 0:
                    idle_time += rng.uniform(15, 30)  # excessive idle
                elif variant == 1:
                    speed += rng.uniform(3, 6)  # overspeed
                elif variant == 2:
                    cycle_time += rng.uniform(15, 30)  # unusual cycle time
                elif variant == 3:
                    fuel_rate += rng.uniform(3, 6)  # fuel anomaly
                elif variant == 4:
                    hydraulic_temp += rng.uniform(15, 25)  # hydraulic temp trend
                elif variant == 5:
                    engine_load = min(100.0, engine_load + rng.uniform(15, 25))  # heavy load
                # variant == 6: combined deterioration handled by scenario module, mild bump here
                else:
                    idle_time += rng.uniform(5, 12)
                    cycle_time += rng.uniform(5, 15)
                    hydraulic_temp += rng.uniform(5, 12)

            rows.append(
                {
                    "timestamp": ts.isoformat(),
                    "machine_id": task["machine_id"],
                    "operator_id": task["operator_id"],
                    "engine_rpm": engine_rpm,
                    "engine_temp": round(engine_temp, 1),
                    "hydraulic_pressure": round(hydraulic_pressure, 1),
                    "hydraulic_temp": round(hydraulic_temp, 1),
                    "fuel_level": round(fuel_level, 1),
                    "fuel_rate": round(fuel_rate, 2),
                    "engine_load": round(engine_load, 1),
                    "speed": round(speed, 1),
                    "cycle_time": round(max(10.0, cycle_time), 1),
                    "idle_time": round(idle_time, 1),
                    "load_cycles": load_cycles,
                    "seatbelt_status": seatbelt,
                    "abnormal_scenario": bool(abnormal_task),
                }
            )
    return pd.DataFrame(rows)


def gen_safety_events(rng: np.random.Generator, tasks: pd.DataFrame) -> pd.DataFrame:
    rows = []
    event_types = ["Proximity Alert", "Seatbelt Violation", "Overspeed", "Unsafe Maneuver", "Hard Stop"]
    for i in range(N_SAFETY_EVENTS):
        task = tasks.sample(random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        ts = datetime.fromisoformat(task["deadline"]) - timedelta(hours=rng.uniform(0, 6))
        severity = rng.choice(["Low", "Medium", "High"], p=[0.55, 0.32, 0.13])
        rows.append(
            {
                "event_id": f"EVT{i+1:04d}",
                "timestamp": ts.isoformat(),
                "machine_id": task["machine_id"],
                "operator_id": task["operator_id"],
                "event_type": rng.choice(event_types),
                "severity": severity,
                "distance": round(rng.uniform(0.5, 8.0), 1),
                "duration": round(rng.uniform(1, 15), 1),
                "zone": task["zone"],
            }
        )
    return pd.DataFrame(rows)


def gen_task_history(rng: np.random.Generator, operators: pd.DataFrame, machines: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i in range(N_TASK_HISTORY):
        operator = operators.sample(random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        machine = machines.sample(random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        task_type = rng.choice(TASK_TYPES)
        weather = rng.choice(WEATHERS, p=[0.55, 0.2, 0.18, 0.07])
        is_rain = weather in ("Rain", "Heavy Rain")
        terrain = rng.choice(TERRAINS, p=[0.15, 0.15, 0.1, 0.6] if is_rain else [0.5, 0.3, 0.15, 0.05])
        terrain_penalty = {"Flat": 0, "Uneven": 4, "Rocky": 7, "Muddy": 10}[terrain]
        load = round(rng.uniform(0.3, 1.0), 2)

        base_cycle = operator["historical_cycle_time"]
        hist_cycle = base_cycle + terrain_penalty * 0.5 + rng.normal(0, 3)

        est_time = round(rng.uniform(40, 140), 1)
        # Relationship 1 & 5 combine into actual time deviation
        skill_idx = SKILL_LEVELS.index(operator["skill_level"])
        age_penalty = machine["age_years"] * 0.4
        rain_penalty = 8 if is_rain else 0
        actual_time = (
            est_time
            + rain_penalty
            + terrain_penalty * 0.6
            + age_penalty
            - skill_idx * 3
            + load * 6
            + rng.normal(0, 5)
        )
        rows.append(
            {
                "task_id": f"HIST{i+1:04d}",
                "task_type": task_type,
                "weather": weather,
                "operator_skill": operator["skill_level"],
                "machine_age": machine["age_years"],
                "terrain": terrain,
                "load": load,
                "historical_cycle_time": round(hist_cycle, 1),
                "estimated_time": est_time,
                "actual_time": round(max(10.0, actual_time), 1),
            }
        )
    return pd.DataFrame(rows)


def gen_training() -> pd.DataFrame:
    rows = [
        {
            "training_id": "TRN001",
            "skill": "cycle_efficiency",
            "title": "Efficient Excavation Positioning",
            "duration": 4,
            "difficulty": "Beginner",
            "resource": "video:excavation_positioning.mp4",
        },
        {
            "training_id": "TRN002",
            "skill": "idle_reduction",
            "title": "Reducing Idle Time During Loading",
            "duration": 5,
            "difficulty": "Beginner",
            "resource": "video:idle_reduction.mp4",
        },
        {
            "training_id": "TRN003",
            "skill": "safe_zone_awareness",
            "title": "Safe Zone Awareness",
            "duration": 6,
            "difficulty": "Intermediate",
            "resource": "video:safe_zone_awareness.mp4",
        },
        {
            "training_id": "TRN004",
            "skill": "wet_terrain_handling",
            "title": "Operating Safely on Wet Terrain",
            "duration": 5,
            "difficulty": "Intermediate",
            "resource": "video:wet_terrain_handling.mp4",
        },
        {
            "training_id": "TRN005",
            "skill": "fuel_efficiency",
            "title": "Fuel-Efficient Operating Patterns",
            "duration": 4,
            "difficulty": "Beginner",
            "resource": "video:fuel_efficiency.mp4",
        },
        {
            "training_id": "TRN006",
            "skill": "proximity_awareness",
            "title": "Proximity Hazard Awareness & Response",
            "duration": 7,
            "difficulty": "Advanced",
            "resource": "video:proximity_awareness.mp4",
        },
    ]
    return pd.DataFrame(rows)


def generate_all(seed: int = SEED) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)

    machines = gen_machines(rng)
    operators = gen_operators(rng)
    environment = gen_environment(rng, site_ids=["SITE01", "SITE02"])
    tasks = gen_tasks(rng, machines, operators)
    telemetry = gen_telemetry(rng, tasks, machines, operators, environment)
    safety_events = gen_safety_events(rng, tasks)
    task_history = gen_task_history(rng, operators, machines)
    training = gen_training()

    return {
        "machines": machines,
        "operators": operators,
        "environment": environment,
        "tasks": tasks,
        "telemetry": telemetry,
        "safety_events": safety_events,
        "task_history": task_history,
        "training": training,
    }


def save_all(datasets: dict[str, pd.DataFrame], out_dir: str = DATA_DIR) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, df in datasets.items():
        df.to_csv(os.path.join(out_dir, f"{name}.csv"), index=False)


if __name__ == "__main__":
    datasets = generate_all()
    save_all(datasets)
    for name, df in datasets.items():
        print(f"{name}: {len(df)} rows, columns={list(df.columns)}")
