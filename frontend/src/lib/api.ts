import type {
  ExpertEpisode,
  ExpertiseEvaluation,
  ExpertiseStatistics,
  HealthState,
  Incident,
  Machine,
  MachineMemory,
  Operator,
  OutcomeResult,
  Recommendation,
  SafetyEvent,
  SimulationStatus,
  SiteCellDetail,
  SiteMap,
  Task,
  TaskPrediction,
  TelemetryReading,
  Training,
  TrainingCompletion,
  TrainingRecommendation,
} from "./types";

const BASE_URL = "/api";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new Error(`POST ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getMachines: () => getJson<Machine[]>("/machines"),
  getMachine: (id: string) => getJson<Machine>(`/machines/${id}`),
  getOperators: () => getJson<Operator[]>("/operators"),
  getOperator: (id: string) => getJson<Operator>(`/operators/${id}`),
  getTasks: (params?: { operator_id?: string; machine_id?: string }) => {
    const qs = params
      ? "?" +
        Object.entries(params)
          .filter(([, v]) => v)
          .map(([k, v]) => `${k}=${encodeURIComponent(v as string)}`)
          .join("&")
      : "";
    return getJson<Task[]>(`/tasks${qs}`);
  },
  getTelemetry: (params?: { machine_id?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.machine_id) qs.set("machine_id", params.machine_id);
    if (params?.limit) qs.set("limit", String(params.limit));
    const s = qs.toString();
    return getJson<TelemetryReading[]>(`/telemetry${s ? `?${s}` : ""}`);
  },
  getSafetyEvents: (params?: { machine_id?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.machine_id) qs.set("machine_id", params.machine_id);
    if (params?.limit) qs.set("limit", String(params.limit));
    const s = qs.toString();
    return getJson<SafetyEvent[]>(`/safety${s ? `?${s}` : ""}`);
  },
  getHealth: (machineId: string) => getJson<HealthState>(`/health/${machineId}`),
  getPrediction: (taskId: string) => getJson<TaskPrediction>(`/predictions/${taskId}`),
  getTraining: () => getJson<Training[]>("/training"),
  getTrainingRecommendation: (operatorId: string) =>
    getJson<{ operator_id: string; recommendation: TrainingRecommendation | null }>(
      `/training/recommendation/${operatorId}`,
    ),
  completeTraining: (payload: { operator_id: string; training_id: string; skill_gap: string; before_cycle_time: number }) =>
    postJson<TrainingCompletion>("/training/complete", payload),
  getTrainingHistory: (operatorId: string) => getJson<TrainingCompletion[]>(`/training/history/${operatorId}`),
  getIncidents: () => getJson<Incident[]>("/incidents"),
  createIncident: (incident: Incident) => postJson<Incident>("/incidents", incident),
  getRecommendation: (machineId: string) => getJson<Recommendation>(`/recommendations/${machineId}`),
  getShiftGreeting: (operatorId: string) =>
    getJson<{
      operator_id: string;
      machine_id: string | null;
      machine_model: string | null;
      previous_shift: { idle_pct: number | null; safety_events: number };
      todays_focus: string;
    }>(`/shift/greeting/${operatorId}`),
  startSimulation: (mode: "scripted" | "random", interval_seconds = 1.0) =>
    postJson<SimulationStatus>("/simulation/start", { mode, interval_seconds }),
  stopSimulation: () => postJson<SimulationStatus>("/simulation/stop"),
  getSimulationStatus: () => getJson<SimulationStatus>("/simulation/status"),

  // CAT Expertise Engine
  getExpertiseEvaluation: (machineId: string) => getJson<ExpertiseEvaluation>(`/expertise/evaluate/${machineId}`),
  getExpertiseEpisodes: (situation?: string) =>
    getJson<{ count: number; episodes: ExpertEpisode[]; data_source: string }>(
      `/expertise/episodes${situation ? `?situation=${encodeURIComponent(situation)}` : ""}`,
    ),
  recordExpertiseOutcome: (payload: { machine_id: string; cycle_time_after: number; successful?: boolean }) =>
    postJson<OutcomeResult>("/expertise/outcome", payload),
  getMachineMemory: () => getJson<MachineMemory>("/expertise/memory"),
  getExpertiseStatistics: () => getJson<ExpertiseStatistics>("/expertise/statistics"),

  // Jobsite Ground Memory
  getSiteMap: () => getJson<SiteMap>("/site/map"),
  getSiteCell: (cellId: string) => getJson<SiteCellDetail>(`/site/cells/${cellId}`),
};
