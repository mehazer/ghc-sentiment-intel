import { api, fmt } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SmartMoney() {
  const [ranking, risk] = await Promise.all([api.ranking(), api.risk()]);
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white">Smart money</h1>
        <p className="text-sm text-muted">Whale accumulation, exchange flow, open interest and funding.</p>
      </header>
      <section className="grid gap-5 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="label">Smart money score by asset</div>
          <div className="mt-3 space-y-3">
            {ranking.map((r) => (
              <div key={r.asset}>
                <div className="flex justify-between text-sm">
                  <span className="font-mono text-white">{r.asset}</span>
                  <span className="text-muted">{fmt(r.smart_money_score, 0)}</span>
                </div>
                <div className="mt-1 h-2 rounded bg-edge">
                  <div className={`h-2 rounded ${r.smart_money_score >= 50 ? "bg-up" : "bg-down"}`}
                    style={{ width: `${Math.min(100, r.smart_money_score)}%` }} />
                </div>
              </div>
            ))}
            {ranking.length === 0 && <p className="text-sm text-muted">No signals yet.</p>}
          </div>
        </div>
        <div className="card">
          <div className="label">Composite risk indicator</div>
          <div className="value text-amber">{fmt(Number(risk.olr ?? 0))}</div>
          <div className="mt-1 text-xs text-muted">Overall liquidation risk</div>
          <div className="mt-4 space-y-1 text-xs">
            {Array.isArray(risk.drivers) && (risk.drivers as string[]).length > 0 ? (
              (risk.drivers as string[]).map((d) => (
                <div key={d} className="border-b border-edge py-1 text-slate-300 last:border-0">{d}</div>
              ))
            ) : <span className="text-muted">No elevated drivers.</span>}
          </div>
        </div>
      </section>
    </div>
  );
}
