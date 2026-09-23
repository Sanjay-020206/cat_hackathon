import { Activity, Gauge, GraduationCap, LayoutDashboard, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/live", label: "Live Operation", icon: Activity },
  { to: "/safety", label: "Safety Center", icon: ShieldAlert },
  { to: "/training", label: "Training Hub", icon: GraduationCap },
  { to: "/shift", label: "Shift Intelligence", icon: Gauge },
];

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0b0f14] text-slate-100">
      <aside className="w-60 shrink-0 border-r border-slate-800 flex flex-col">
        <div className="px-5 py-5 border-b border-slate-800">
          <p className="text-sm font-semibold tracking-wide text-slate-100">CAT Operator Intelligence</p>
          <p className="text-xs text-slate-500 mt-0.5">Closed-loop decision support</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-sky-500/10 text-sky-400"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-slate-800 text-xs text-slate-600">
          Local-first prototype · No cloud dependency
        </div>
      </aside>
      <main className="flex-1 min-w-0 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-6">{children}</div>
      </main>
    </div>
  );
}
