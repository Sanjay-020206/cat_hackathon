import { Map as MapIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { SiteCellDetail, SiteCellSummary, SiteMap as SiteMapData } from "../lib/types";

const DIFFICULTY_COLOR: Record<string, string> = {
  LOW: "bg-emerald-500/70",
  MEDIUM: "bg-amber-500/70",
  HIGH: "bg-red-500/70",
};

function cellColor(cell: SiteCellSummary): string {
  if (cell.observation_count === 0) return "bg-slate-700/40 light:bg-slate-200";
  return DIFFICULTY_COLOR[cell.excavation_difficulty] ?? "bg-slate-600";
}

export function SiteMap() {
  const [map, setMap] = useState<SiteMapData | null>(null);
  const [selectedCell, setSelectedCell] = useState<SiteCellDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    api
      .getSiteMap()
      .then((m) => {
        setMap(m);
        setError(null);
      })
      .catch((e) => setError(String(e)));
  };

  useEffect(load, []);

  const handleCellClick = (cellId: string) => {
    api.getSiteCell(cellId).then(setSelectedCell).catch(() => setSelectedCell(null));
  };

  const cellsByPosition = new Map<string, SiteCellSummary>();
  map?.cells.forEach((c) => cellsByPosition.set(`${c.x},${c.y}`, c));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100 light:text-slate-900 flex items-center gap-2">
          <MapIcon size={20} className="text-sky-400" /> Jobsite Ground Memory
        </h1>
        <p className="text-sm text-slate-500 light:text-slate-500">
          Estimated ground condition built up from simulated machine response, not measured soil composition.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-800 light:border-red-300 bg-red-950/40 light:bg-red-50 px-4 py-3 text-sm text-red-300 light:text-red-700">
          Failed to load site map: {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[auto_1fr] gap-6">
        <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4">
          {map && (
            <div
              className="grid gap-1"
              style={{ gridTemplateColumns: `repeat(${map.width}, minmax(0, 1fr))` }}
            >
              {Array.from({ length: map.height }).map((_, y) =>
                Array.from({ length: map.width }).map((__, x) => {
                  const cell = cellsByPosition.get(`${x},${y}`);
                  if (!cell) return <div key={`${x}-${y}`} className="w-9 h-9" />;
                  return (
                    <button
                      key={cell.cell_id}
                      onClick={() => handleCellClick(cell.cell_id)}
                      title={`${cell.cell_id}: ${cell.estimated_material}`}
                      className={`w-9 h-9 rounded-md ${cellColor(cell)} hover:ring-2 hover:ring-sky-400 transition-all flex items-center justify-center text-[10px] font-medium text-white/90`}
                    >
                      {cell.cell_id}
                    </button>
                  );
                }),
              )}
            </div>
          )}

          <div className="flex flex-wrap gap-3 pt-4 text-xs text-slate-400 light:text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-emerald-500/70 inline-block" /> Low resistance
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-amber-500/70 inline-block" /> Medium resistance
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-red-500/70 inline-block" /> High resistance
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-slate-700/40 light:bg-slate-200 inline-block" /> Unknown
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4">
          <h2 className="text-sm font-medium text-slate-300 light:text-slate-600 uppercase tracking-wide mb-3">
            Area Detail
          </h2>
          {selectedCell ? (
            <div className="space-y-2 text-sm text-slate-300 light:text-slate-700">
              <p className="text-lg font-medium text-slate-100 light:text-slate-900">Area {selectedCell.cell_id}</p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
                <span className="text-slate-500 light:text-slate-400">Estimated ground</span>
                <span>{selectedCell.estimated_material.replace(/_/g, " ")}</span>
                <span className="text-slate-500 light:text-slate-400">Confidence</span>
                <span>{Math.round(selectedCell.material_confidence * 100)}%</span>
                <span className="text-slate-500 light:text-slate-400">Resistance</span>
                <span>{selectedCell.resistance_score.toFixed(2)}</span>
                <span className="text-slate-500 light:text-slate-400">Difficulty</span>
                <span>{selectedCell.excavation_difficulty}</span>
                <span className="text-slate-500 light:text-slate-400">Avg cycle time</span>
                <span>{selectedCell.average_cycle_time.toFixed(1)}s</span>
                <span className="text-slate-500 light:text-slate-400">Avg energy/cycle</span>
                <span>{selectedCell.average_energy_per_cycle.toFixed(2)}</span>
                <span className="text-slate-500 light:text-slate-400">Observations</span>
                <span>{selectedCell.observation_count}</span>
                <span className="text-slate-500 light:text-slate-400">Successful patterns</span>
                <span>{selectedCell.successful_episode_count}</span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500 light:text-slate-400">Click a cell on the map to see its detail.</p>
          )}
        </div>
      </div>
    </div>
  );
}
