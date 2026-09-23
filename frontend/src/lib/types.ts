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
  // Present only on the live WebSocket stream -- the CAT Expertise Engine's evaluation
  // of the same reading, computed server-side alongside the risk/NBA context.
  expertise?: ExpertiseEvaluation | null;
  ml_anomaly?: { anomaly_flag: boolean; anomaly_score: number } | null;
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

// ---- CAT Expertise Engine ----

export interface OperatingSituation {
  machine_id: string;
  machine_model: string;
  attachment_type: string;
  task_type: string;
  hydraulic_pressure: number;
  engine_load: number;
  rpm: number;
  cycle_time: number;
  fuel_rate: number;
  machine_speed: number;
  material_resistance: number;
  penetration_rate: number;
  vibration_level: number;
  energy_per_cycle: number;
  position_x: number;
  position_y: number;
  depth: number;
  operator_experience_level: string;
  timestamp: string;
}

export interface GroundEstimate {
  cell_id: string;
  estimated_material: string;
  material_confidence: number;
  resistance_score: number | null;
  excavation_difficulty: string;
  observation_count: number;
  confidence_note: string | null;
}

export interface EnergyForecast {
  cell_id: string;
  expected_resistance: string;
  expected_energy_per_cycle: number | null;
  expected_energy_label?: string;
  expected_cycle_time: number | null;
  expected_difficulty: string;
  confidence: number;
  note: string | null;
}

export interface ExpertMoment {
  triggered: boolean;
  situation: string;
  reason: string;
}

export interface ExpertMatch {
  episode_id: string;
  similarity: number;
  action_sequence: string[];
  successful: boolean;
  cycle_time: number;
  energy_per_cycle: number;
  operator_experience_level: string;
}

export interface ExpertPattern {
  pattern: string[];
  supporting_episode_count: number;
  method: string;
}

export interface ExpertConfidence {
  score: number;
  tier: "high" | "low" | "none";
  components: Record<string, number>;
}

export interface ExpertNextBestAction {
  action_sequence: string[];
  reason: string;
  confidence: number;
  priority: "high" | "medium";
}

export interface ExpertiseEvaluation {
  machine_id: string;
  situation: string;
  operating_situation: OperatingSituation;
  area: { cell_id: string; x: number; y: number; depth: number };
  ground_estimate: GroundEstimate;
  energy_forecast: EnergyForecast;
  expert_moment: ExpertMoment;
  matches: ExpertMatch[];
  pattern: ExpertPattern | null;
  confidence: ExpertConfidence;
  next_best_action: ExpertNextBestAction | null;
  data_source: string;
}

export interface ExpertEpisode {
  episode_id: string;
  machine_model: string;
  attachment: string;
  task: string;
  situation: string;
  context: Record<string, number>;
  operator_profile: { experience_level: string };
  action_sequence: string[];
  outcome: { cycle_time: number; energy_per_cycle: number; successful: boolean };
  cell_id: string | null;
  quality_score: number;
  is_synthetic: boolean;
}

export interface ExpertiseStatistics {
  areas_mapped: number;
  total_areas: number;
  known_high_resistance_areas: number;
  known_low_resistance_areas: number;
  unknown_areas: number;
  successful_patterns: number;
  new_patterns_learned_today: number;
  as_of: string;
  data_source: string;
}

export interface MachineMemory {
  total_episodes: number;
  trusted_episodes: number;
  episodes_by_situation: Record<string, number>;
  new_episodes_this_session: number;
  data_source: string;
}

export interface OutcomeResult {
  cell_id: string;
  material_confidence_before: number;
  material_confidence_after: number;
  observation_count: number;
  new_episode_stored: boolean;
  episode_id: string | null;
  updated_at: string | null;
}

export interface SiteCellSummary {
  cell_id: string;
  x: number;
  y: number;
  estimated_material: string;
  material_confidence: number;
  excavation_difficulty: "LOW" | "MEDIUM" | "HIGH";
  observation_count: number;
  successful_episode_count: number;
}

export interface SiteMap {
  width: number;
  height: number;
  cells: SiteCellSummary[];
  data_source: string;
}

export interface SiteCellDetail extends SiteCellSummary {
  resistance_score: number;
  average_hydraulic_load: number;
  average_engine_load: number;
  average_energy_per_cycle: number;
  average_cycle_time: number;
  last_updated: string | null;
  recent_history: { timestamp: string; resistance: number; successful: boolean }[];
}
