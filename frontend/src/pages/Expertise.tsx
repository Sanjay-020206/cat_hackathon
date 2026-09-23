import { Award, Battery, Brain, CheckCircle2, MapPin, Sparkles, TriangleAlert, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../lib/api";
import type { ExpertiseEvaluation, ExpertiseStatistics, Machine, MachineMemory } from "../lib/types";

function formatStep(step: string): string {
  return step.replace(/_/g, " ");
}

export function Expertise() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState("");
  const [evaluation, setEvaluation] = useState<ExpertiseEvaluation | null>(null);
  const [stats, setStats] = useState<ExpertiseStatistics | null>(null);
  const [memory, setMemory] = useState<MachineMemory | null>(null);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getMachines().then((data) => {
      setMachines(data);
      if (data.length > 0) setSelectedMachineId(data[0].machine_id);
    });
    api.getExpertiseStatistics().then(setStats).catch(() => setStats(null));
    api.getMachineMemory().then(setMemory).catch(() => setMemory(null));
  }, []);

  const load = () => {
    if (!selectedMachineId) return;
    api
      .getExpertiseEvaluation(selectedMachineId)
      .then((e) => {
        setEvaluation(e);
        setError(null);
      })
      .catch((e) => setError(String(e)));
  };

  useEffect(load, [selectedMachineId]);

  const handleOutcome = async (successful: boolean) => {
    if (!evaluation) return;
    setRecording(true);
    try {
      await api.recordExpertiseOutcome({
        machine_id: evaluation.machine_id,
        cycle_time_after: evaluation.operating_situation.cycle_time * (successful ? 0.85 : 1.05),
        successful,
      });
      load();
      api.getExpertiseStatistics().then(setStats).catch(() => {});
      api.getMachineMemory().then(setMemory).catch(() => {});
    } finally {
      setRecording(false);
    }
  };

  const moment = evaluation?.expert_moment;
  const nba = evaluation?.next_best_action;
  const noReliableExperience = moment && !moment.triggered && moment.reason === "NO_RELIABLE_EXPERIENCE_FOUND";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 light:text-slate-900 flex items-center gap-2">
            <Brain size={20} className="text-violet-400" /> CAT Expertise Engine
          </h1>
          <p className="text-sm text-slate-500 light:text-slate-500">
            Bringing the right experience to the operator at the right moment.
          </p>
        </div>
        <select
          value={selectedMachineId}
          onChange={(e) => setSelectedMachineId(e.target.value)}
          className="rounded-lg border border-slate-700 light:border-slate-300 bg-slate-900 light:bg-white px-3 py-2 text-sm text-slate-200 light:text-slate-800"
        >
          {machines.map((m) => (
            <option key={m.machine_id} value={m.machine_id}>
              {m.machine_id} · {m.model}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="rounded-lg border border-red-800 light:border-red-300 bg-red-950/40 light:bg-red-50 px-4 py-3 text-sm text-red-300 light:text-red-700">
          Failed to load expertise evaluation: {error}
        </div>
      )}

      {evaluation && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Situation" value={evaluation.situation.replace(/_/g, " ")} icon={Sparkles} accent="violet" />
            <StatCard
              label="Current Area"
              value={evaluation.area.cell_id}
              icon={MapPin}
              accent="sky"
              sub={`x${evaluation.area.x}, y${evaluation.area.y}`}
            />
            <StatCard
              label="Ground Condition"
              value={evaluation.ground_estimate.estimated_material.replace(/_/g, " ")}
              icon={TriangleAlert}
              accent={evaluation.ground_estimate.estimated_material === "UNKNOWN" ? "amber" : "sky"}
              sub={`${Math.round(evaluation.ground_estimate.material_confidence * 100)}% confidence`}
            />
            <StatCard
              label="Expected Energy"
              value={evaluation.energy_forecast.expected_energy_label ?? "UNKNOWN"}
              icon={Battery}
              accent={evaluation.energy_forecast.expected_energy_label === "VERY_HIGH" ? "red" : "amber"}
            />
          </div>

          <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-300 light:text-slate-600">
                {moment?.triggered ? (
                  <Sparkles size={16} className="text-violet-400" />
                ) : noReliableExperience ? (
                  <XCircle size={16} className="text-slate-500" />
                ) : (
                  <CheckCircle2 size={16} className="text-emerald-400" />
                )}
                {moment?.triggered
                  ? "Expert Moment"
                  : noReliableExperience
                    ? "No Reliable Experience Found"
                    : "No Intervention Needed"}
              </div>
              {evaluation.confidence.tier !== "none" && (
                <StatusBadge label={evaluation.confidence.tier === "high" ? "High" : "Low"} colorKey={evaluation.confidence.tier === "high" ? "Low" : "Watch"} />
              )}
            </div>

            {moment?.triggered && nba ? (
              <>
                <div className="space-y-1">
                  <p className="text-lg font-medium text-slate-100 light:text-slate-900">
                    {nba.action_sequence.map(formatStep).join(" → ")}
                  </p>
                  <p className="text-sm text-slate-400 light:text-slate-500">{nba.reason}</p>
                </div>
                <div className="flex items-center gap-4 text-sm text-slate-300 light:text-slate-700 pt-1">
                  <span>
                    Priority: <span className="capitalize text-slate-100 light:text-slate-900">{nba.priority}</span>
                  </span>
                  <span>
                    Confidence:{" "}
                    <span className="text-slate-100 light:text-slate-900">{Math.round(nba.confidence * 100)}%</span>
                  </span>
                </div>
              </>
            ) : noReliableExperience ? (
              <p className="text-sm text-slate-400 light:text-slate-500">
                This area and operating situation differ significantly from stored experience.
                Continue normal operation. Additional observations will improve site memory.
              </p>
            ) : (
              <p className="text-sm text-slate-400 light:text-slate-500">
                Operation is within normal range -- no expert intervention required right now.
              </p>
            )}

            {evaluation.matches.length > 0 && (
              <div className="pt-3 border-t border-slate-800 light:border-slate-200">
                <p className="text-xs uppercase tracking-wide text-slate-500 light:text-slate-400 mb-2">
                  Similar historical episodes ({evaluation.matches.length})
                </p>
                <ul className="space-y-1.5">
                  {evaluation.matches.slice(0, 4).map((m) => (
                    <li key={m.episode_id} className="flex items-center justify-between text-sm text-slate-300 light:text-slate-600">
                      <span className="flex items-center gap-1.5">
                        {m.successful ? (
                          <CheckCircle2 size={13} className="text-emerald-400" />
                        ) : (
                          <XCircle size={13} className="text-red-400" />
                        )}
                        {m.episode_id} · {m.operator_experience_level} · {m.action_sequence.map(formatStep).join(" → ")}
                      </span>
                      <span className="text-slate-500 light:text-slate-400">{Math.round(m.similarity * 100)}% similar</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {evaluation.pattern && (
              <div className="pt-2 text-xs text-slate-500 light:text-slate-400">
                Pattern support: {evaluation.pattern.supporting_episode_count} episode(s) ·{" "}
                {evaluation.pattern.method.replace(/_/g, " ")}
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => handleOutcome(true)}
                disabled={recording}
                className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
              >
                <CheckCircle2 size={15} /> Record Successful Outcome
              </button>
              <button
                onClick={() => handleOutcome(false)}
                disabled={recording}
                className="flex items-center gap-1.5 rounded-lg bg-slate-800 light:bg-slate-200 px-3 py-1.5 text-sm font-medium text-slate-200 light:text-slate-700 disabled:opacity-50"
              >
                <XCircle size={15} /> Record Unsuccessful
              </button>
            </div>
          </div>
        </>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4 space-y-2">
          <h2 className="text-sm font-medium text-slate-300 light:text-slate-600 uppercase tracking-wide flex items-center gap-1.5">
            <MapPin size={15} /> Site Memory
          </h2>
          {stats ? (
            <ul className="text-sm text-slate-300 light:text-slate-700 space-y-1">
              <li className="flex justify-between">
                <span className="text-slate-500 light:text-slate-400">Areas mapped</span>
                <span>
                  {stats.areas_mapped} / {stats.total_areas}
                </span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-500 light:text-slate-400">Known high-resistance areas</span>
                <span>{stats.known_high_resistance_areas}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-500 light:text-slate-400">Known low-resistance areas</span>
                <span>{stats.known_low_resistance_areas}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-500 light:text-slate-400">Unknown areas</span>
                <span>{stats.unknown_areas}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-500 light:text-slate-400">New patterns learned this session</span>
                <span>{stats.new_patterns_learned_today}</span>
              </li>
            </ul>
          ) : (
            <p className="text-sm text-slate-500 light:text-slate-400">Loading...</p>
          )}
        </div>

        <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4 space-y-2">
          <h2 className="text-sm font-medium text-slate-300 light:text-slate-600 uppercase tracking-wide flex items-center gap-1.5">
            <Award size={15} /> Machine Memory
          </h2>
          {memory ? (
            <>
              <ul className="text-sm text-slate-300 light:text-slate-700 space-y-1">
                <li className="flex justify-between">
                  <span className="text-slate-500 light:text-slate-400">Trusted episodes</span>
                  <span>
                    {memory.trusted_episodes} / {memory.total_episodes}
                  </span>
                </li>
              </ul>
              <div className="pt-1 flex flex-wrap gap-1.5">
                {Object.entries(memory.episodes_by_situation).map(([situation, count]) => (
                  <span
                    key={situation}
                    className="text-xs rounded-full border border-slate-700 light:border-slate-300 px-2 py-0.5 text-slate-400 light:text-slate-500"
                  >
                    {situation.replace(/_/g, " ")}: {count}
                  </span>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500 light:text-slate-400">Loading...</p>
          )}
        </div>
      </div>

      <p className="text-xs text-slate-600 light:text-slate-400">
        This system is a decision-support prototype using synthetic demo data (episodes and jobsite ground memory).
        It does not detect exact soil composition and does not control the machine.
      </p>
    </div>
  );
}
