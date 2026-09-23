import { Moon, Sun } from "lucide-react";
import { useTheme } from "../lib/theme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      className="flex items-center gap-2 rounded-lg border border-slate-800 light:border-slate-300 bg-slate-900/60 light:bg-white px-2.5 py-1.5 text-xs font-medium text-slate-300 light:text-slate-600 hover:bg-slate-800 light:hover:bg-slate-100 transition-colors"
    >
      {theme === "dark" ? <Moon size={14} /> : <Sun size={14} />}
      {theme === "dark" ? "Dark" : "Light"}
    </button>
  );
}
