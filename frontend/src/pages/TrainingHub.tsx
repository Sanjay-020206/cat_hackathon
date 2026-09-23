import { BookOpen, CheckCircle2, Clock } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Training } from "../lib/types";

export function TrainingHub() {
  const [modules, setModules] = useState<Training[]>([]);
  const [completed, setCompleted] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api.getTraining().then(setModules);
  }, []);

  const toggleComplete = (id: string) => {
    setCompleted((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Training Hub</h1>
        <p className="text-sm text-slate-500">
          Personalized micro-training, recommended when a recurring behavior pattern is detected.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {modules.map((m) => (
          <div key={m.training_id} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <BookOpen size={17} className="text-sky-400" />
                <p className="font-medium text-slate-100">{m.title}</p>
              </div>
              <span className="text-xs rounded-full border border-slate-700 px-2 py-0.5 text-slate-400">
                {m.difficulty}
              </span>
            </div>
            <p className="text-sm text-slate-400 flex items-center gap-1.5">
              <Clock size={14} /> {m.duration} minutes · skill: {m.skill.replace(/_/g, " ")}
            </p>
            <button
              onClick={() => toggleComplete(m.training_id)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium ${
                completed[m.training_id]
                  ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                  : "bg-slate-800 text-slate-200 hover:bg-slate-700"
              }`}
            >
              <CheckCircle2 size={15} />
              {completed[m.training_id] ? "Completed" : "Mark as Completed"}
            </button>
          </div>
        ))}
        {modules.length === 0 && <p className="text-sm text-slate-500">Loading training catalog...</p>}
      </div>
    </div>
  );
}
