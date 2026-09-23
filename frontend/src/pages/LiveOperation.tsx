import { AlertOctagon, Play, Radio, Square } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { NBACard } from "../components/NBACard";
import { RiskTrendChart } from "../components/RiskTrendChart";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../lib/api";
import { useTelemetryStream } from "../lib/ws";

const STALE_THRESHOLD_SECONDS = 12;

export function LiveOperation() {
  const { latest, history, connectionState, lastReceivedAt } = useTelemetryStream();
  const [simRunning, setSimRunning] = useState(false);
  const [riskSeries, setRiskSeries] = useState<{ t: string; risk: number }[]>([]);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const secondsSinceLastReading = lastReceivedAt !== null ? Math.max(0, Math.round((now - lastReceivedAt) / 1000)) : null;
  const telemetryDegraded =
    simRunning && secondsSinceLastReading !== null && secondsSinceLastReading > STALE_THRESHOLD_SECONDS;

  useEffect(() => {
    api
      .getSimulationStatus()
      .then((s) => setSimRunning(s.running))
      .catch(() => {});
  }, []);

  // The live recommendation arrives already computed on each WebSocket tick (Context
  // Engine + NBA run server-side per reading) -- no separate REST poll needed, which
  // also avoids the mismatch of showing DB-historical risk instead of the live stream's.
  const recommendation = latest?.recommendation ?? null;

  useEffect(() => {
    if (!recommendation) return;
    setRiskSeries((prev) => [...prev.slice(-29), { t: new Date().toLocaleTimeString(), risk: recommendation.risk_score }]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [latest?.timestamp]);

  const stageLabel = latest?.stage_label ?? "--";

  const handleStart = async () => {
    await api.startSimulation("scripted", 1.0);
    setSimRunning(true);
  };
  const handleStop = async () => {
    await api.stopSimulation();
    setSimRunning(false);
  };

  const connectionColor = useMemo(() => {
    if (connectionState === "open") return "text-emerald-400";
    if (connectionState === "connecting") return "text-amber-400";
    return "text-red-400";
  }, [connectionState]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Live Operation</h1>
          <p className="text-sm text-slate-500 flex items-center gap-2">
            <Radio size={14} className={connectionColor} /> {connectionState}
            {latest && <span> · stage: {stageLabel}</span>}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleStart}
            disabled={simRunning}
            className="flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            <Play size={15} /> Start Demo
          </button>
          <button
            onClick={handleStop}
            disabled={!simRunning}
            className="flex items-center gap-1.5 rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-slate-200 disabled:opacity-40"
          >
            <Square size={15} /> Stop
          </button>
        </div>
      </div>

      {telemetryDegraded && (
        <div className="rounded-lg border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300 flex items-center gap-2">
          <AlertOctagon size={16} />
          <span>
            Telemetry quality degraded — last update {secondsSinceLastReading}s ago. Prediction confidence reduced.
          </span>
        </div>
      )}

      {latest?.note && (
        <div className="rounded-lg border border-sky-900 bg-sky-950/40 px-4 py-2 text-sm text-sky-300">
          {latest.note}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Cycle Time" value={latest ? `${latest.cycle_time}s` : "--"} icon={Radio} accent="sky" />
        <StatCard label="Idle Time" value={latest ? `${latest.idle_time}s` : "--"} icon={Radio} accent="amber" />
        <StatCard label="Fuel Rate" value={latest ? `${latest.fuel_rate} L/h` : "--"} icon={Radio} accent="violet" />
        <StatCard
          label="Hydraulic Temp"
          value={latest ? `${latest.hydraulic_temp}°C` : "--"}
          icon={Radio}
          accent={latest && latest.hydraulic_temp > 75 ? "red" : "sky"}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-medium text-slate-300 uppercase tracking-wide">Risk Trend</h2>
            {recommendation && (
              <div className="flex gap-2">
                <StatusBadge label={recommendation.risk_level} />
                <StatusBadge label={recommendation.risk_trend} />
              </div>
            )}
          </div>
          <RiskTrendChart data={riskSeries} />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
          <h2 className="text-sm font-medium text-slate-300 uppercase tracking-wide mb-2">Machine Health</h2>
          {latest ? (
            <ul className="text-sm text-slate-300 space-y-1.5">
              <li className="flex justify-between">
                <span className="text-slate-500">Engine RPM</span>
                <span>{latest.engine_rpm}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-500">Engine Temp</span>
                <span>{latest.engine_temp}°C</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-500">Engine Load</span>
                <span>{latest.engine_load}%</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-500">Hydraulic Pressure</span>
                <span>{latest.hydraulic_pressure} bar</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-500">Seatbelt</span>
                <span>{latest.seatbelt_status}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-500">Proximity Events</span>
                <span>{latest.proximity_events ?? 0}</span>
              </li>
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Start the demo simulation to see live telemetry.</p>
          )}
        </div>
      </div>

      {recommendation && (
        <div>
          <h2 className="text-sm font-medium text-slate-300 uppercase tracking-wide mb-2">
            Live Next Best Action
          </h2>
          <NBACard recommendation={recommendation} />
        </div>
      )}

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="text-sm font-medium text-slate-300 uppercase tracking-wide mb-2">Recent Readings</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-400">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500">
                <th className="py-1.5 pr-4">Time</th>
                <th className="py-1.5 pr-4">Stage</th>
                <th className="py-1.5 pr-4">Cycle</th>
                <th className="py-1.5 pr-4">Idle</th>
                <th className="py-1.5 pr-4">Hyd Temp</th>
              </tr>
            </thead>
            <tbody>
              {history
                .slice()
                .reverse()
                .slice(0, 10)
                .map((r, i) => (
                  <tr key={i} className="border-b border-slate-800/60">
                    <td className="py-1.5 pr-4">{new Date(r.timestamp).toLocaleTimeString()}</td>
                    <td className="py-1.5 pr-4">{r.stage_label}</td>
                    <td className="py-1.5 pr-4">{r.cycle_time}s</td>
                    <td className="py-1.5 pr-4">{r.idle_time}s</td>
                    <td className="py-1.5 pr-4">{r.hydraulic_temp}°C</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
