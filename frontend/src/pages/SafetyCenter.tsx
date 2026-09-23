import { FilePlus, ShieldAlert, ShieldCheck, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../lib/api";
import type { Incident, Machine, Recommendation, SafetyEvent } from "../lib/types";

const EMPTY_FORM = {
  event_type: "Proximity Alert",
  severity: "Medium",
  zone: "Zone A",
  trigger: "",
  action_taken: "",
  outcome: "",
};

export function SafetyCenter() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState("");
  const [events, setEvents] = useState<SafetyEvent[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.getMachines().then((data) => {
      setMachines(data);
      if (data.length > 0) setSelectedMachineId(data[0].machine_id);
    });
    api.getIncidents().then(setIncidents).catch(() => setIncidents([]));
  }, []);

  useEffect(() => {
    if (!selectedMachineId) return;
    api.getSafetyEvents({ machine_id: selectedMachineId, limit: 20 }).then(setEvents);
    api.getRecommendation(selectedMachineId).then(setRecommendation).catch(() => setRecommendation(null));
  }, [selectedMachineId]);

  const highSeverityCount = events.filter((e) => e.severity === "High").length;

  const handleLogIncident = async () => {
    if (!selectedMachineId) return;
    setSubmitting(true);
    try {
      const incident: Incident = {
        incident_id: `INC${Date.now()}`,
        timestamp: new Date().toISOString(),
        machine_id: selectedMachineId,
        operator_id: recommendation?.operator_id ?? "UNKNOWN",
        site_zone: form.zone,
        event_type: form.event_type,
        severity: form.severity,
        trigger: form.trigger || "Manually logged by operator",
        action_taken: form.action_taken || "Not specified",
        outcome: form.outcome || "Pending review",
      };
      const created = await api.createIncident(incident);
      setIncidents((prev) => [created, ...prev]);
      setForm(EMPTY_FORM);
      setShowForm(false);
    } finally {
      setSubmitting(false);
    }
  };

  const selectClass =
    "rounded-lg border border-slate-700 light:border-slate-300 bg-slate-950 light:bg-white px-3 py-2 text-sm text-slate-200 light:text-slate-800";
  const inputClass =
    "rounded-lg border border-slate-700 light:border-slate-300 bg-slate-950 light:bg-white px-3 py-2 text-sm text-slate-200 light:text-slate-800";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 light:text-slate-900">Safety Center</h1>
          <p className="text-sm text-slate-500 light:text-slate-500">
            Seatbelt, proximity and incident monitoring
          </p>
        </div>
        <div className="flex gap-2">
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
          <button
            onClick={() => setShowForm((s) => !s)}
            className="flex items-center gap-1.5 rounded-lg bg-slate-800 light:bg-slate-200 px-3 py-2 text-sm font-medium text-slate-200 light:text-slate-700 hover:bg-slate-700 light:hover:bg-slate-300"
          >
            <FilePlus size={15} /> Log Incident
          </button>
        </div>
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
        <div className="rounded-xl border border-orange-900 light:border-orange-300 bg-orange-950/30 light:bg-orange-50 p-4">
          <p className="text-sm font-medium text-orange-300 light:text-orange-700">
            {recommendation.next_best_action.action_label}
          </p>
          <p className="text-xs text-orange-400/80 light:text-orange-600 mt-1">
            {recommendation.explanation.evidence}
          </p>
        </div>
      )}

      {showForm && (
        <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4 space-y-3">
          <h2 className="text-sm font-medium text-slate-300 light:text-slate-600 uppercase tracking-wide">
            New Incident
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <select
              value={form.event_type}
              onChange={(e) => setForm({ ...form, event_type: e.target.value })}
              className={selectClass}
            >
              {["Proximity Alert", "Seatbelt Violation", "Overspeed", "Unsafe Maneuver", "Hard Stop"].map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <select
              value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}
              className={selectClass}
            >
              {["Low", "Medium", "High"].map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <input
              value={form.zone}
              onChange={(e) => setForm({ ...form, zone: e.target.value })}
              placeholder="Zone"
              className={inputClass}
            />
            <input
              value={form.trigger}
              onChange={(e) => setForm({ ...form, trigger: e.target.value })}
              placeholder="What triggered this?"
              className={`${inputClass} md:col-span-3`}
            />
            <input
              value={form.action_taken}
              onChange={(e) => setForm({ ...form, action_taken: e.target.value })}
              placeholder="Action taken"
              className={`${inputClass} md:col-span-3`}
            />
            <input
              value={form.outcome}
              onChange={(e) => setForm({ ...form, outcome: e.target.value })}
              placeholder="Outcome"
              className={`${inputClass} md:col-span-3`}
            />
          </div>
          <button
            onClick={handleLogIncident}
            disabled={submitting}
            className="rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {submitting ? "Saving..." : "Save Incident"}
          </button>
        </div>
      )}

      <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4">
        <h2 className="text-sm font-medium text-slate-300 light:text-slate-600 uppercase tracking-wide mb-3">
          Logged Incidents
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="border-b border-slate-800 light:border-slate-200 text-slate-500 light:text-slate-400 text-xs uppercase">
                <th className="py-2 pr-4">Time</th>
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4">Severity</th>
                <th className="py-2 pr-4">Zone</th>
                <th className="py-2 pr-4">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((i) => (
                <tr
                  key={i.incident_id}
                  className="border-b border-slate-800/60 light:border-slate-200/80 text-slate-300 light:text-slate-700"
                >
                  <td className="py-2 pr-4">{new Date(i.timestamp).toLocaleString()}</td>
                  <td className="py-2 pr-4">{i.event_type}</td>
                  <td className="py-2 pr-4">
                    <StatusBadge label={i.severity} />
                  </td>
                  <td className="py-2 pr-4">{i.site_zone}</td>
                  <td className="py-2 pr-4">{i.outcome}</td>
                </tr>
              ))}
              {incidents.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-4 text-center text-slate-500 light:text-slate-400">
                    No incidents logged yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4">
        <h2 className="text-sm font-medium text-slate-300 light:text-slate-600 uppercase tracking-wide mb-3">
          Safety Event History
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="border-b border-slate-800 light:border-slate-200 text-slate-500 light:text-slate-400 text-xs uppercase">
                <th className="py-2 pr-4">Time</th>
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4">Severity</th>
                <th className="py-2 pr-4">Zone</th>
                <th className="py-2 pr-4">Distance</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr
                  key={e.event_id}
                  className="border-b border-slate-800/60 light:border-slate-200/80 text-slate-300 light:text-slate-700"
                >
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
                  <td colSpan={5} className="py-4 text-center text-slate-500 light:text-slate-400">
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
