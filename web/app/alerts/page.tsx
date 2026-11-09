import { api, fmt } from "@/lib/api";

export const dynamic = "force-dynamic";

const TONE: Record<string, string> = {
  early_accumulation: "bg-up/15 text-up",
  breakout_watch: "bg-amber/15 text-amber",
  fomo_warning: "bg-down/15 text-down",
  possible_top: "bg-down/15 text-down",
};

export default async function Alerts() {
  const alerts = await api.alerts();
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white">Alerts</h1>
        <p className="text-sm text-muted">Every alert carries its reason, confidence and expected impact.</p>
      </header>
      <section className="space-y-3">
        {alerts.map((a) => (
          <article key={a.id} className="card">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <span className="font-mono text-lg text-white">{a.asset}</span>
                <span className={`pill ${TONE[a.kind] ?? "bg-edge text-muted"}`}>{a.kind.replaceAll("_", " ")}</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted">
                <span>Confidence {fmt(a.confidence * 100, 0)}%</span>
                <span>Impact {a.expected_impact}</span>
                <time className="font-mono">{new Date(a.created_at).toLocaleString()}</time>
              </div>
            </div>
            <p className="mt-2 text-sm text-slate-300">{a.reason}</p>
          </article>
        ))}
        {alerts.length === 0 && (
          <div className="card text-sm text-muted">No alerts yet. Evaluate an asset after computing its signal.</div>
        )}
      </section>
    </div>
  );
}
