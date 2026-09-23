export interface Machine {
  machine_id: string;
  model: string;
  machine_type: string;
  age_years: number;
  engine_hours: number;
  maintenance_status: string;
}

export interface Operator {
  operator_id: string;
  skill_level: string;
  experience_months: number;
  certifications: string;
  historical_cycle_time: number;
  historical_idle_rate: number;
  historical_safety_events: number;
}

export interface Task {
  task_id: string;
  machine_id: string;
  operator_id: string;
  task_type: string;
  material: string;
  target_quantity: number;
  deadline: string;
  zone: string;
  original_estimated_time: number;
}

export interface TelemetryReading {
  id?: number;
  timestamp: string;
  machine_id: string;
  operator_id: string;
  engine_rpm: number;
  engine_temp: number;
  hydraulic_pressure: number;
  hydraulic_temp: number;
  fuel_level: number;
  fuel_rate: number;
  engine_load: number;
  speed: number;
  cycle_time: number;
  idle_time: number;
  load_cycles: number;
  seatbelt_status: string;
  abnormal_scenario?: boolean;
  proximity_alert?: boolean;
  proximity_events?: number;
  stage_label?: string;
  note?: string;
  weather?: string;
  ground_condition?: string;
  recommendation?: Recommendation | null;
}

export interface SafetyEvent {
  event_id: string;
  timestamp: string;
  machine_id: string;
  operator_id: string;
  event_type: string;
  severity: string;
  distance: number;
  duration: number;
  zone: string;
}

export interface Training {
  training_id: string;
  skill: string;
  title: string;
  duration: number;
  difficulty: string;
  resource: string;
}

export interface Incident {
  incident_id: string;
  timestamp: string;
  machine_id: string;
  operator_id: string;
  site_zone: string;
  event_type: string;
  severity: string;
  trigger: string;
  action_taken: string;
  outcome: string;
}

export interface Contributor {
  factor: string;
  value: string | number | boolean;
  importance: number;
}

export interface NextBestAction {
  action: string;
  action_label: string;
  priority: "Low" | "Medium" | "High";
  confidence: number;
}

export interface Explanation {
  detection: string;
  evidence: string;
  explanation: string;
  recommendation: string;
  priority: string;
  confidence: number;
  source: string;
}

export interface Recommendation {
  machine_id: string;
  operator_id: string;
  risk_level: "Low" | "Moderate" | "Elevated" | "High";
  risk_score: number;
  risk_trend: "Increasing" | "Decreasing" | "Stable";
  contributors: Contributor[];
  next_best_action: NextBestAction;
  explanation: Explanation;
}

export interface HealthState {
  machine_id: string;
  state: "Normal" | "Watch" | "Elevated" | "Critical";
  score: number;
  as_of: string;
}

export interface TaskPrediction {
  task_id: string;
  original_estimated_time: number;
  predicted_duration: number;
  confidence: number | null;
  explanation: { factor: string; raw_value: unknown; impact_minutes: number }[];
  deadline_at_risk?: boolean;
  note?: string;
}

export interface TrainingRecommendation {
  skill_gap: string;
  training_id: string;
  title: string;
  duration_minutes: number;
  reason: string;
  current_cycle_time: number;
}

export interface TrainingCompletion {
  operator_id: string;
  training_id: string;
  skill_gap: string;
  completed_at: string;
  before: number;
  after: number;
  improvement_pct: number;
}

export interface SimulationStatus {
  running: boolean;
  mode: string | null;
  ticks_emitted: number;
}
