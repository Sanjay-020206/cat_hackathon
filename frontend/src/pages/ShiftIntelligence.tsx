import { Fuel, Gauge, ShieldCheck, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import { StatCard } from "../components/StatCard";
import { api } from "../lib/api";
import type { Machine, Recommendation } from "../lib/types";

export function ShiftIntelligence() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState("");
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);

  useEffect(() => {
    api.getMachines().then((data) => {
      setMachines(data);
      if (data.length > 0) setSelectedMachineId(data[0].machine_id);
    });
  }, []);

  useEffect(() => {
    if (!selectedMachineId) return;
    api.getRecommendation(selectedMachineId).then(setRecommendation).catch(() => setRecommendation(null));
  }, [selectedMachineId]);

  const productivity = recommendation ? Math.round((1 - recommendation.risk_score) * 100) : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 light:text-slate-900">Shift Intelligence</h1>
          <p className="text-sm text-slate-500 light:text-slate-500">
            End-of-shift summary and recommendations for next shift
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Productivity"
          value={productivity !== null ? `${productivity}%` : "--"}
          icon={TrendingUp}
          accent="violet"
        />
        <StatCard
          label="Safety"
          value={recommendation?.risk_level ?? "--"}
          icon={ShieldCheck}
          accent={recommendation?.risk_level === "Low" ? "emerald" : "amber"}
        />
        <StatCard label="Machine Health" value="--" icon={Gauge} accent="sky" sub="see Live Operation" />
        <StatCard label="Fuel Efficiency" value="--" icon={Fuel} accent="amber" sub="see Live Operation" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4 space-y-2">
          <h2 className="text-sm font-medium text-emerald-400 light:text-emerald-700 uppercase tracking-wide">
            Positive Outcomes
          </h2>
          <ul className="text-sm text-slate-300 light:text-slate-700 space-y-1.5 list-disc list-inside">
            <li>Cycle efficiency held within operator baseline for most of the shift.</li>
            <li>No unresolved safety violations by end of shift.</li>
            <li>Machine health remained in the Normal/Watch range.</li>
          </ul>
        </div>

        <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4 space-y-2">
          <h2 className="text-sm font-medium text-amber-400 light:text-amber-700 uppercase tracking-wide">
            Attention Areas
          </h2>
          <ul className="text-sm text-slate-300 light:text-slate-700 space-y-1.5 list-disc list-inside">
            {recommendation && recommendation.contributors.length > 0 ? (
              recommendation.contributors.slice(0, 4).map((c) => (
                <li key={c.factor} className="capitalize">
                  {c.factor.replace(/_/g, " ")}
                </li>
              ))
            ) : (
              <li>No significant attention areas detected this shift.</li>
            )}
          </ul>
        </div>
      </div>

      <div className="rounded-xl border border-sky-900 light:border-sky-300 bg-sky-950/30 light:bg-sky-50 p-4">
        <h2 className="text-sm font-medium text-sky-300 light:text-sky-700 uppercase tracking-wide mb-1">
          Next Shift Recommendation
        </h2>
        <p className="text-sm text-sky-200 light:text-sky-800">
          {recommendation && recommendation.next_best_action.action !== "continue_operation"
            ? `Complete relevant training before the next shift: ${recommendation.explanation.evidence}`
            : "No specific training required before the next shift; continue current operating patterns."}
        </p>
      </div>
    </div>
  );
}
