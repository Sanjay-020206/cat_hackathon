const COLORS: Record<string, string> = {
  Normal: "bg-emerald-500/15 text-emerald-400 light:text-emerald-700 border-emerald-500/30",
  Low: "bg-emerald-500/15 text-emerald-400 light:text-emerald-700 border-emerald-500/30",
  Watch: "bg-amber-500/15 text-amber-400 light:text-amber-700 border-amber-500/30",
  Medium: "bg-amber-500/15 text-amber-400 light:text-amber-700 border-amber-500/30",
  Moderate: "bg-amber-500/15 text-amber-400 light:text-amber-700 border-amber-500/30",
  Elevated: "bg-orange-500/15 text-orange-400 light:text-orange-700 border-orange-500/30",
  Critical: "bg-red-500/15 text-red-400 light:text-red-700 border-red-500/30",
  High: "bg-red-500/15 text-red-400 light:text-red-700 border-red-500/30",
  Increasing: "bg-red-500/15 text-red-400 light:text-red-700 border-red-500/30",
  Decreasing: "bg-emerald-500/15 text-emerald-400 light:text-emerald-700 border-emerald-500/30",
  Stable: "bg-slate-500/15 text-slate-300 light:text-slate-600 border-slate-500/30",
  "AT RISK": "bg-orange-500/15 text-orange-400 light:text-orange-700 border-orange-500/30",
  "ON TRACK": "bg-emerald-500/15 text-emerald-400 light:text-emerald-700 border-emerald-500/30",
};

export function StatusBadge({ label, colorKey }: { label: string; colorKey?: string }) {
  const cls =
    COLORS[colorKey ?? label] ?? "bg-slate-500/15 text-slate-300 light:text-slate-600 border-slate-500/30";
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}
