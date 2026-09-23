import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTheme } from "../lib/theme";

export interface RiskPoint {
  t: string;
  risk: number;
}

export function RiskTrendChart({ data }: { data: RiskPoint[] }) {
  const { theme } = useTheme();
  const isLight = theme === "light";
  const tickColor = isLight ? "#64748b" : "#64748b";
  const tooltipBg = isLight ? "#ffffff" : "#0f172a";
  const tooltipBorder = isLight ? "#e2e8f0" : "#1e293b";
  const labelColor = isLight ? "#475569" : "#94a3b8";

  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <defs>
            <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f87171" stopOpacity={0.5} />
              <stop offset="100%" stopColor="#f87171" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="t" tick={{ fontSize: 11, fill: tickColor }} axisLine={false} tickLine={false} />
          <YAxis
            domain={[0, 1]}
            tick={{ fontSize: 11, fill: tickColor }}
            axisLine={false}
            tickLine={false}
            width={32}
          />
          <Tooltip
            contentStyle={{ background: tooltipBg, border: `1px solid ${tooltipBorder}`, borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: labelColor }}
          />
          <Area type="monotone" dataKey="risk" stroke="#f87171" fill="url(#riskGradient)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
