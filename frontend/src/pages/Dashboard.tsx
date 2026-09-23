import { Activity, Gauge, HardHat, ShieldCheck, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { NBACard } from "../components/NBACard";
import { StatCard } from "../components/StatCard";
import { TaskCard } from "../components/TaskCard";
import { api } from "../lib/api";
import type { HealthState, Machine, Operator, Recommendation, Task } from "../lib/types";

export function Dashboard() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState<string>("");
  const [operator, setOperator] = useState<Operator | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [health, setHealth] = useState<HealthState | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMachines()
      .then((data) => {
        setMachines(data);
        if (data.length > 0) setSelectedMachineId(data[0].machine_id);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!selectedMachineId) return;

    let cancelled = false;

    async function load() {
      try {
        const [health, recommendation, telemetry] = await Promise.all([
          api.getHealth(selectedMachineId),
          api.getRecommendation(selectedMachineId),
          api.getTelemetry({ machine_id: selectedMachineId, limit: 1 }),
        ]);
        if (cancelled) return;
        setHealth(health);
        setRecommendation(recommendation);

        const operatorId = telemetry[0]?.operator_id ?? recommendation.operator_id;
        const [operatorData, taskData] = await Promise.all([
          api.getOperator(operatorId),
          api.getTasks({ operator_id: operatorId }),
        ]);
        if (cancelled) return;
        setOperator(operatorData);
        setTasks(taskData);
        setError(null);
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [selectedMachineId]);

  const currentTask = tasks[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Operator Dashboard</h1>
          <p className="text-sm text-slate-500">
            {operator ? `${operator.operator_id} · ${operator.skill_level}` : "Loading operator..."}
          </p>
        </div>
        <select
          value={selectedMachineId}
          onChange={(e) => setSelectedMachineId(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
        >
          {machines.map((m) => (
            <option key={m.machine_id} value={m.machine_id}>
              {m.machine_id} · {m.model}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="rounded-lg border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">
          Failed to load dashboard data: {error}. Is the backend running on port 8000?
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Machine Health"
          value={health ? `${health.score.toFixed(0)}%` : "--"}
          icon={Wrench}
          accent="sky"
          sub={health?.state}
        />
        <StatCard
          label="Safety"
          value={recommendation?.risk_level ?? "--"}
          icon={ShieldCheck}
          accent={recommendation?.risk_level === "Low" ? "emerald" : "amber"}
        />
        <StatCard
          label="Productivity"
          value={currentTask ? "On pace" : "--"}
          icon={Activity}
          accent="violet"
          sub={currentTask ? `${currentTask.task_type}` : undefined}
        />
        <StatCard
          label="Risk Trend"
          value={recommendation?.risk_trend ?? "--"}
          icon={Gauge}
          accent={
            recommendation?.risk_trend === "Increasing"
              ? "red"
              : recommendation?.risk_trend === "Decreasing"
                ? "emerald"
                : "amber"
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-slate-300 uppercase tracking-wide flex items-center gap-2">
            <HardHat size={16} /> Current Task
          </h2>
          {currentTask ? <TaskCard task={currentTask} /> : <p className="text-sm text-slate-500">No active task.</p>}

          <h2 className="text-sm font-medium text-slate-300 uppercase tracking-wide pt-2">Today's Tasks</h2>
          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
            {tasks.slice(0, 6).map((t) => (
              <TaskCard key={t.task_id} task={t} />
            ))}
            {tasks.length === 0 && <p className="text-sm text-slate-500">No scheduled tasks found.</p>}
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-sm font-medium text-slate-300 uppercase tracking-wide">Next Best Action</h2>
          <NBACard recommendation={recommendation} />
        </div>
      </div>
    </div>
  );
}
