import { AlertTriangle, ArrowRight, CheckCircle2 } from "lucide-react";
import type { Recommendation } from "../lib/types";
import { StatusBadge } from "./StatusBadge";

export function NBACard({ recommendation }: { recommendation: Recommendation | null }) {
  if (!recommendation) {
    return (
      <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-5 text-slate-400 light:text-slate-500 text-sm">
        No recommendation available yet.
      </div>
    );
  }

  const { next_best_action, explanation, risk_level, risk_trend, contributors } = recommendation;
  const isNormal = next_best_action.action === "continue_operation";

  return (
    <div className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-300 light:text-slate-600 text-xs uppercase tracking-wide">
          {isNormal ? (
            <CheckCircle2 size={16} className="text-emerald-400" />
          ) : (
            <AlertTriangle size={16} className="text-orange-400" />
          )}
          Next Best Action
        </div>
        <div className="flex gap-2">
          <StatusBadge label={risk_level} />
          <StatusBadge label={risk_trend} />
        </div>
      </div>

      <div className="flex items-start gap-2">
        <ArrowRight size={18} className="mt-0.5 shrink-0 text-sky-400" />
        <p className="text-lg font-medium text-slate-100 light:text-slate-900">{next_best_action.action_label}</p>
      </div>

      <div className="text-sm text-slate-400 light:text-slate-500 space-y-1">
        <p>
          <span className="text-slate-500 light:text-slate-400">Reason: </span>
          {explanation.evidence}
        </p>
        <div className="flex items-center gap-4 pt-1">
          <span>
            Priority: <span className="text-slate-200 light:text-slate-800">{next_best_action.priority}</span>
          </span>
          <span>
            Confidence:{" "}
            <span className="text-slate-200 light:text-slate-800">
              {Math.round(next_best_action.confidence * 100)}%
            </span>
          </span>
        </div>
      </div>

      {contributors.length > 0 && (
        <div className="pt-2 border-t border-slate-800 light:border-slate-200">
          <p className="text-xs uppercase tracking-wide text-slate-500 light:text-slate-400 mb-2">
            Contributing factors
          </p>
          <ul className="space-y-1">
            {contributors.slice(0, 4).map((c) => (
              <li key={c.factor} className="flex justify-between text-sm text-slate-300 light:text-slate-600">
                <span className="capitalize">{c.factor.replace(/_/g, " ")}</span>
                <span className="text-slate-500 light:text-slate-400">{String(c.value)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
