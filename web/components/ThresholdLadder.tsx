import { fmt } from "@/lib/api";

const ZONES = [
  { key: "sell_2", label: "S2", tone: "text-up" },
  { key: "sell_1", label: "S1", tone: "text-up" },
  { key: "between", label: "Balance", tone: "text-slate-300" },
  { key: "buy_1", label: "B1", tone: "text-down" },
  { key: "buy_2", label: "B2", tone: "text-down" },
];

export function ThresholdLadder({
  balance, deviation, zone,
}: { balance: number; deviation: number; zone: string }) {
  const levels = [
    { label: "S2", value: balance * 2.0, pct: 100 },
    { label: "S1", value: balance * 1.5, pct: 50 },
    { label: "Balance", value: balance, pct: 0 },
    { label: "B1", value: balance * 0.5, pct: -50 },
    { label: "B2", value: balance * 0.1, pct: -90 },
  ];
  const marker = Math.max(0, Math.min(100, ((deviation + 90) / 190) * 100));
  return (
    <div className="card">
      <div className="flex items-baseline justify-between">
        <div className="label">GHC threshold ladder</div>
        <div className={`pill ${deviation >= 0 ? "bg-up/15 text-up" : "bg-down/15 text-down"}`}>
          {deviation >= 0 ? "+" : ""}{fmt(deviation, 1)}% deviation
        </div>
      </div>
      <div className="relative mt-5 h-64">
        {levels.map((lvl, i) => (
          <div key={lvl.label} className="absolute left-0 right-0 flex items-center gap-3"
            style={{ top: `${(i / (levels.length - 1)) * 100}%` }}>
            <span className="w-16 text-right font-mono text-xs text-muted">{lvl.label}</span>
            <div className={`h-px flex-1 ${lvl.label === "Balance" ? "bg-slate-500" : "bg-edge"}`} />
            <span className="w-24 font-mono text-xs tabular-nums text-slate-400">{fmt(lvl.value, 0)}</span>
          </div>
        ))}
        <div className="absolute right-0 top-0 bottom-0 w-8">
          <div className="absolute -left-2 h-3 w-3 rounded-full bg-amber shadow-[0_0_12px_rgba(240,185,11,0.8)]"
            style={{ top: `calc(${100 - marker}% - 6px)` }} />
        </div>
      </div>
      <div className="mt-2 text-xs text-muted">
        Current zone: <span className="text-slate-200">{ZONES.find((z) => z.key === zone)?.label ?? zone}</span>
      </div>
    </div>
  );
}
