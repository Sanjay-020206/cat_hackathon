import type { Task } from "../lib/types";
import { StatusBadge } from "./StatusBadge";

export function TaskCard({ task, aiEta, status }: { task: Task; aiEta?: number; status?: string }) {
  return (
    <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4 space-y-2">
      <div className="flex items-center justify-between">
        <p className="font-medium text-slate-100 light:text-slate-900">{task.task_type}</p>
        {status && <StatusBadge label={status} />}
      </div>
      <p className="text-sm text-slate-400 light:text-slate-500">
        Target: {task.target_quantity} {task.material.toLowerCase()} · Zone {task.zone}
      </p>
      <div className="flex justify-between text-sm text-slate-300 light:text-slate-700 pt-1">
        <span>Original ETA: {task.original_estimated_time} min</span>
        {aiEta !== undefined && <span>AI ETA: {aiEta.toFixed(0)} min</span>}
      </div>
      <p className="text-xs text-slate-500 light:text-slate-400">
        Deadline: {new Date(task.deadline).toLocaleString()}
      </p>
    </div>
  );
}
