import { BookOpen, CheckCircle2, Clock, Sparkles, TrendingDown } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Operator, Training, TrainingCompletion, TrainingRecommendation } from "../lib/types";

export function TrainingHub() {
  const [modules, setModules] = useState<Training[]>([]);
  const [operators, setOperators] = useState<Operator[]>([]);
  const [selectedOperatorId, setSelectedOperatorId] = useState("");
  const [recommendation, setRecommendation] = useState<TrainingRecommendation | null>(null);
  const [history, setHistory] = useState<TrainingCompletion[]>([]);
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    api.getTraining().then(setModules);
    api.getOperators().then((data) => {
      setOperators(data);
      if (data.length > 0) setSelectedOperatorId(data[0].operator_id);
    });
  }, []);

  useEffect(() => {
    if (!selectedOperatorId) return;
    api
      .getTrainingRecommendation(selectedOperatorId)
      .then((r) => setRecommendation(r.recommendation))
      .catch(() => setRecommendation(null));
    api
      .getTrainingHistory(selectedOperatorId)
      .then(setHistory)
      .catch(() => setHistory([]));
  }, [selectedOperatorId]);

  const handleComplete = async () => {
    if (!recommendation) return;
    setCompleting(true);
    try {
      const record = await api.completeTraining({
        operator_id: selectedOperatorId,
        training_id: recommendation.training_id,
        skill_gap: recommendation.skill_gap,
        before_cycle_time: recommendation.current_cycle_time,
      });
      setHistory((prev) => [...prev, record]);
    } finally {
      setCompleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 light:text-slate-900">Training Hub</h1>
          <p className="text-sm text-slate-500 light:text-slate-500">
            Personalized micro-training, recommended when a recurring behavior pattern is detected.
          </p>
        </div>
        <select
          value={selectedOperatorId}
          onChange={(e) => setSelectedOperatorId(e.target.value)}
          className="rounded-lg border border-slate-700 light:border-slate-300 bg-slate-900 light:bg-white px-3 py-2 text-sm text-slate-200 light:text-slate-800"
        >
          {operators.map((o) => (
            <option key={o.operator_id} value={o.operator_id}>
              {o.operator_id} · {o.skill_level}
            </option>
          ))}
        </select>
      </div>

      <div className="rounded-xl border border-sky-900 light:border-sky-300 bg-sky-950/30 light:bg-sky-50 p-5 space-y-3">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-sky-400 light:text-sky-700">
          <Sparkles size={16} /> Recommended for you
        </div>
        {recommendation ? (
          <>
            <p className="text-lg font-medium text-slate-100 light:text-slate-900">{recommendation.title}</p>
            <p className="text-sm text-slate-400 light:text-slate-500 flex items-center gap-1.5">
              <Clock size={14} /> {recommendation.duration_minutes} minutes
            </p>
            <p className="text-sm text-slate-300 light:text-slate-700">
              <span className="text-slate-500 light:text-slate-400">Reason: </span>
              {recommendation.reason}
            </p>
            <button
              onClick={handleComplete}
              disabled={completing}
              className="flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
            >
              <CheckCircle2 size={15} />
              {completing ? "Recording..." : "Complete Training"}
            </button>
          </>
        ) : (
          <p className="text-sm text-slate-400 light:text-slate-500">
            No specific training required right now; this operator's behavior is within their baseline.
          </p>
        )}
      </div>

      {history.length > 0 && (
        <div className="rounded-xl border border-emerald-900 light:border-emerald-300 bg-emerald-950/20 light:bg-emerald-50 p-4 space-y-2">
          <h2 className="text-sm font-medium text-emerald-400 light:text-emerald-700 uppercase tracking-wide flex items-center gap-1.5">
            <TrendingDown size={15} /> Observed Impact
          </h2>
          {history.map((h, i) => (
            <div key={i} className="flex items-center justify-between text-sm text-slate-300 light:text-slate-700">
              <span>{h.training_id}</span>
              <span>
                {h.before}s → {h.after}s{" "}
                <span className="text-emerald-400 light:text-emerald-700">({h.improvement_pct}% improvement)</span>
              </span>
            </div>
          ))}
        </div>
      )}

      <h2 className="text-sm font-medium text-slate-300 light:text-slate-600 uppercase tracking-wide pt-2">
        Full Catalog
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {modules.map((m) => (
          <div
            key={m.training_id}
            className="rounded-xl border border-slate-800 light:border-slate-200 bg-slate-900/60 light:bg-white p-4 space-y-2"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <BookOpen size={17} className="text-sky-400" />
                <p className="font-medium text-slate-100 light:text-slate-900">{m.title}</p>
              </div>
              <span className="text-xs rounded-full border border-slate-700 light:border-slate-300 px-2 py-0.5 text-slate-400 light:text-slate-500">
                {m.difficulty}
              </span>
            </div>
            <p className="text-sm text-slate-400 light:text-slate-500 flex items-center gap-1.5">
              <Clock size={14} /> {m.duration} minutes · skill: {m.skill.replace(/_/g, " ")}
            </p>
          </div>
        ))}
        {modules.length === 0 && (
          <p className="text-sm text-slate-500 light:text-slate-400">Loading training catalog...</p>
        )}
      </div>
    </div>
  );
}
