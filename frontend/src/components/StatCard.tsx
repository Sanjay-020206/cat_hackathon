import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  accent?: "emerald" | "amber" | "red" | "sky" | "violet";
  sub?: string;
}

const ACCENTS: Record<string, string> = {
  emerald: "text-emerald-400 bg-emerald-500/10",
  amber: "text-amber-400 bg-amber-500/10",
  red: "text-red-400 bg-red-500/10",
  sky: "text-sky-400 bg-sky-500/10",
  violet: "text-violet-400 bg-violet-500/10",
};

export function StatCard({ label, value, icon: Icon, accent = "sky", sub }: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex items-start gap-3">
      <div className={`rounded-lg p-2 ${ACCENTS[accent]}`}>
        <Icon size={20} />
      </div>
      <div className="min-w-0">
        <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
        <p className="text-xl font-semibold text-slate-100 truncate">{value}</p>
        {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}
