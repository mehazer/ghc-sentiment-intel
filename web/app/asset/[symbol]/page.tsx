import { api, fmt } from "@/lib/api";
import { Sparkline } from "@/components/Sparkline";
import { ScoreGauge } from "@/components/ScoreGauge";

export const dynamic = "force-dynamic";

export default async function AssetPage({ params }: { params: { symbol: string } }) {
  const symbol = params.symbol.toUpperCase();
  const [history, why] = await Promise.all([api.history(symbol), api.why(symbol)]);
  const latest = history[history.length - 1];
  const points = history
    .filter((h) => h.timestamp)
    .map((h) => ({ time: h.timestamp as string, value: h.alpha_score }));

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-mono text-2xl font-semibold text-white">{symbol}</h1>
          <p className="text-sm text-muted">{latest?.classification ?? "No signal yet"}</p>
        </div>
        {latest && <ScoreGauge score={latest.alpha_score} label="Alpha score" />}
      </header>

      <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {latest && ([
          ["Sentiment", latest.sentiment_score],
          ["Attention", latest.attention_score],
          ["Velocity", latest.velocity_score],
          ["Smart money", latest.smart_money_score],
        ] as const).map(([label, value]) => (
          <div key={label} className="card">
            <div className="label">{label}</div>
            <div className="value">{fmt(value, 0)}</div>
            <div className="mt-2 h-1.5 rounded bg-edge">
              <div className="h-1.5 rounded bg-up" style={{ width: `${Math.min(100, value)}%` }} />
            </div>
          </div>
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="label">Alpha timeline</div>
          <Sparkline points={points} />
        </div>
        <div className="card">
          <div className="label">Why the score changed</div>
          {why && Object.keys(why).length > 0 ? (
            <div className="mt-3 space-y-2 text-sm text-slate-300">
              <p className="text-muted">{String((why as Record<string, unknown>).summary ?? "")}</p>
              {typeof (why as Record<string, unknown>).delta === "number" && (
                <p>Delta: <span className="font-mono text-white">{fmt((why as { delta: number }).delta)}</span></p>
              )}
              {typeof (why as Record<string, unknown>).driver === "string" && (
                <p>Driver: <span className="text-amber">{String((why as { driver: string }).driver)}</span></p>
              )}
            </div>
          ) : <p className="mt-3 text-sm text-muted">Not enough history to compare runs.</p>}
          {latest?.explanation?.components && (
            <div className="mt-4 space-y-1 text-xs text-muted">
              {Object.entries(latest.explanation.components).map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-edge py-1 last:border-0">
                  <span>{k.replaceAll("_", " ")}</span>
                  <span className="font-mono text-slate-300">{fmt(Number(v), 0)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
