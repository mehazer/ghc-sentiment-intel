import Link from "next/link";
import { api, fmt, signed, zoneLabel } from "@/lib/api";
import { ScoreGauge } from "@/components/ScoreGauge";
import { ThresholdLadder } from "@/components/ThresholdLadder";

export const dynamic = "force-dynamic";

export default async function Overview() {
  const [ranking, state, playbook, alerts] = await Promise.all([
    api.ranking(), api.state(), api.playbook(), api.alerts(),
  ]);
  const top = ranking.slice(0, 5);
  const opportunity = ranking.find((r) => r.alpha_score >= 71) ?? ranking[0];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white">Market overview</h1>
          <p className="text-sm text-muted">Attention, sentiment and smart-money alignment across tracked assets.</p>
        </div>
        {state && (
          <div className="flex items-center gap-3 text-sm">
            <span className="pill bg-edge text-slate-300">{zoneLabel[state.zone] ?? state.zone}</span>
            <span className={`pill ${state.deviation_pct >= 0 ? "bg-up/15 text-up" : "bg-down/15 text-down"}`}>
              {signed(state.deviation_pct)}%
            </span>
          </div>
        )}
      </header>

      <section className="grid gap-5 lg:grid-cols-3">
        <div className="card lg:col-span-1">
          <div className="label">Top opportunity</div>
          {opportunity ? (
            <>
              <div className="mt-1 flex items-baseline gap-3">
                <span className="text-3xl font-bold text-white">{opportunity.asset}</span>
                <span className="text-sm text-muted">{opportunity.classification}</span>
              </div>
              <ScoreGauge score={opportunity.alpha_score} label="Alpha score" />
              <p className="mt-2 text-xs leading-relaxed text-muted">{opportunity.explanation?.summary}</p>
              <Link href={`/asset/${opportunity.asset}`} className="mt-4 inline-block text-sm text-amber hover:underline">
                View asset detail →
              </Link>
            </>
          ) : (
            <p className="mt-4 text-sm text-muted">
              No signals yet. Ingest posts and market data, then compute a score.
            </p>
          )}
        </div>

        <div className="card lg:col-span-2">
          <div className="label">Alpha ranking</div>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wider text-muted">
                <tr>
                  <th className="pb-2">Asset</th><th className="pb-2 text-right">Alpha</th>
                  <th className="pb-2 text-right">Sent</th><th className="pb-2 text-right">Attn</th>
                  <th className="pb-2 text-right">SM</th><th className="pb-2 text-right">Conf</th>
                  <th className="pb-2">Class</th>
                </tr>
              </thead>
              <tbody className="font-mono tabular-nums">
                {ranking.map((r) => (
                  <tr key={r.asset} className="border-t border-edge">
                    <td className="py-2">
                      <Link href={`/asset/${r.asset}`} className="text-white hover:text-amber">{r.asset}</Link>
                    </td>
                    <td className="py-2 text-right">{fmt(r.alpha_score)}</td>
                    <td className="py-2 text-right text-slate-400">{fmt(r.sentiment_score, 0)}</td>
                    <td className="py-2 text-right text-slate-400">{fmt(r.attention_score, 0)}</td>
                    <td className="py-2 text-right text-slate-400">{fmt(r.smart_money_score, 0)}</td>
                    <td className="py-2 text-right text-slate-400">{fmt(r.confidence * 100, 0)}%</td>
                    <td className="py-2 text-xs text-muted">{r.classification}</td>
                  </tr>
                ))}
                {ranking.length === 0 && (
                  <tr><td colSpan={7} className="py-6 text-center text-muted">No signals computed yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        {state ? (
          <ThresholdLadder balance={state.balance_line} deviation={state.deviation_pct} zone={state.zone} />
        ) : (
          <div className="card"><div className="label">GHC threshold ladder</div>
            <p className="mt-3 text-sm text-muted">Set the balance line in the GHC Console to activate the ladder.</p></div>
        )}

        <div className="card">
          <div className="label">Playbook now</div>
          <div className="mt-2 text-sm text-slate-300">{zoneLabel[playbook?.zone ?? ""] ?? "Not configured"}</div>
          <ul className="mt-3 space-y-2 text-sm text-slate-300">
            {(playbook?.actions ?? []).slice(0, 5).map((a) => (
              <li key={a} className="flex gap-2"><span className="text-amber">›</span><span>{a}</span></li>
            ))}
          </ul>
          <Link href="/ghc" className="mt-4 inline-block text-sm text-amber hover:underline">Open GHC console →</Link>
        </div>

        <div className="card">
          <div className="label">Live alerts</div>
          <ul className="mt-3 space-y-3">
            {alerts.slice(0, 4).map((a) => (
              <li key={a.id} className="border-b border-edge pb-2 last:border-0">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm text-white">{a.asset}</span>
                  <span className={`pill ${a.expected_impact === "high" ? "bg-down/15 text-down" : "bg-edge text-muted"}`}>
                    {a.kind.replaceAll("_", " ")}
                  </span>
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-muted">{a.reason}</p>
              </li>
            ))}
            {alerts.length === 0 && <li className="text-sm text-muted">No alerts triggered.</li>}
          </ul>
          <Link href="/alerts" className="mt-4 inline-block text-sm text-amber hover:underline">All alerts →</Link>
        </div>
      </section>

      <section className="card">
        <div className="label">Trend radar</div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {top.map((t) => (
            <div key={t.asset} className="rounded-lg border border-edge p-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm text-white">{t.asset}</span>
                <span className="font-mono text-xs text-muted">{fmt(t.alpha_score, 0)}</span>
              </div>
              <div className="mt-2 h-1.5 w-full rounded bg-edge">
                <div className="h-1.5 rounded bg-amber" style={{ width: `${Math.min(100, t.attention_score)}%` }} />
              </div>
              <div className="mt-2 text-[11px] text-muted">Attention {fmt(t.attention_score, 0)} · Velocity {fmt(t.velocity_score, 0)}</div>
            </div>
          ))}
          {top.length === 0 && <p className="text-sm text-muted">Trend radar fills once signals exist.</p>}
        </div>
      </section>
    </div>
  );
}
