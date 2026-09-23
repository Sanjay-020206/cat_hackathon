import { ShieldAlert, ShieldCheck, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../lib/api";
import type { Machine, Recommendation, SafetyEvent } from "../lib/types";

export function SafetyCenter() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState("");
  const [events, setEvents] = useState<SafetyEvent[]>([]);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);

  useEffect(() => {
    api.getMachines().then((data) => {
      setMachines(data);
      if (data.length > 0) setSelectedMachineId(data[0].machine_id);
    });
  }, []);

  useEffect(() => {
    if (!selectedMachineId) return;
    api.getSafetyEvents({ machine_id: selectedMachineId, limit: 20 }).then(setEvents);
    api.getRecommendation(selectedMachineId).then(setRecommendation).catch(() => setRecommendation(null));
  }, [selectedMachineId]);

  const highSeverityCount = events.filter((e) => e.severity === "High").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Safety Center</h1>
          <p className="text-sm text-slate-500">Seatbelt, proximity and incident monitoring</p>
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Safety State"
          value={recommendation?.risk_level ?? "--"}
          icon={recommendation?.risk_level === "Low" ? ShieldCheck : ShieldAlert}
          accent={recommendation?.risk_level === "Low" ? "emerald" : "amber"}
        />
        <StatCard label="Recorded Events" value={String(events.length)} icon={TriangleAlert} accent="sky" />
        <StatCard label="High Severity" value={String(highSeverityCount)} icon={TriangleAlert} accent="red" />
        <StatCard label="Risk Trend" value={recommendation?.risk_trend ?? "--"} icon={ShieldAlert} accent="violet" />
      </div>

      {recommendation && recommendation.next_best_action.action !== "continue_operation" && (
        <div className="rounded-xl border border-orange-900 bg-orange-950/30 p-4">
          <p className="text-sm font-medium text-orange-300">{recommendation.next_best_action.action_label}</p>
          <p className="text-xs text-orange-400/80 mt-1">{recommendation.explanation.evidence}</p>
        </div>
      )}

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="text-sm font-medium text-slate-300 uppercase tracking-wide mb-3">Incident History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 text-xs uppercase">
                <th className="py-2 pr-4">Time</th>
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4">Severity</th>
                <th className="py-2 pr-4">Zone</th>
                <th className="py-2 pr-4">Distance</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.event_id} className="border-b border-slate-800/60 text-slate-300">
                  <td className="py-2 pr-4">{new Date(e.timestamp).toLocaleString()}</td>
                  <td className="py-2 pr-4">{e.event_type}</td>
                  <td className="py-2 pr-4">
                    <StatusBadge label={e.severity} />
                  </td>
                  <td className="py-2 pr-4">{e.zone}</td>
                  <td className="py-2 pr-4">{e.distance} m</td>
                </tr>
              ))}
              {events.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-4 text-center text-slate-500">
                    No safety events recorded for this machine.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
