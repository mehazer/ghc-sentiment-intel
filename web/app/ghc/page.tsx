import { api, fmt, signed, zoneLabel } from "@/lib/api";
import { ThresholdLadder } from "@/components/ThresholdLadder";

export const dynamic = "force-dynamic";

export default async function GHCConsole() {
  const [state, playbook, trades] = await Promise.all([api.state(), api.playbook(), api.trades()]);
  const open = trades.filter((t) => t.status === "open");
  const outliers = open.filter((t) => t.is_outlier);
  const dailyPnl = open.reduce((sum, t) => sum + t.pnl_usd, 0);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">GHC console</h1>
          <p className="text-sm text-muted">Gradual Hedge Cropping thresholds, playbook and basket risk.</p>
        </div>
        {state && (
          <div className={`pill ${state.daily_pnl_forecast >= 0 ? "bg-up/15 text-up" : "bg-down/15 text-down"}`}>
            Daily PnL forecast {signed(state.daily_pnl_forecast, 0)}
          </div>
        )}
      </header>

      {!state ? (
        <div className="card text-sm text-muted">
          No GHC state yet. POST a balance line and current equity to <code className="text-amber">/api/ghc/balance</code> to activate the ladder.
        </div>
      ) : (
        <section className="grid gap-5 lg:grid-cols-2">
          <ThresholdLadder balance={state.balance_line} deviation={state.deviation_pct} zone={state.zone} />
          <div className="card">
            <div className="label">Action plan</div>
            <div className="mt-1 text-sm text-white">{zoneLabel[state.zone] ?? state.zone}</div>
            <ol className="mt-3 space-y-2 text-sm text-slate-300">
              {(playbook?.actions ?? []).map((a, i) => (
                <li key={a} className="flex gap-3">
                  <span className="font-mono text-xs text-muted">{String(i + 1).padStart(2, "0")}</span>
                  <span>{a}</span>
                </li>
              ))}
            </ol>
            <div className="mt-5 space-y-1 border-t border-edge pt-3 text-[11px] leading-relaxed text-muted">
              {(playbook?.guards ?? []).map((g) => <p key={g}>• {g}</p>)}
            </div>
          </div>
        </section>
      )}

      <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Open trades", String(open.length)],
          ["Outliers", String(outliers.length)],
          ["Unrealised PnL", fmt(dailyPnl, 0)],
          ["CSI", fmt(state?.csi ?? 0, 0)],
        ].map(([label, value]) => (
          <div key={label} className="card">
            <div className="label">{label}</div>
            <div className="value">{value}</div>
          </div>
        ))}
      </section>

      <section className="card">
        <div className="label">Trade list</div>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wider text-muted">
              <tr>
                <th className="pb-2">Symbol</th><th className="pb-2">Basket</th><th className="pb-2 text-right">Size</th>
                <th className="pb-2 text-right">Dev %</th><th className="pb-2 text-right">PnL</th><th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody className="font-mono tabular-nums">
              {trades.map((t) => (
                <tr key={t.id} className="border-t border-edge">
                  <td className="py-2 text-white">{t.symbol}</td>
                  <td className="py-2 text-slate-400">{t.basket}/{t.side}</td>
                  <td className="py-2 text-right text-slate-400">{fmt(t.size_usd, 0)}</td>
                  <td className="py-2 text-right text-slate-400">{signed(t.deviation_pct, 1)}</td>
                  <td className={`py-2 text-right ${t.pnl_pct >= 0 ? "text-up" : "text-down"}`}>{signed(t.pnl_pct, 2)}</td>
                  <td className="py-2">
                    <span className={`pill ${t.is_outlier ? "bg-down/15 text-down" : "bg-edge text-muted"}`}>
                      {t.is_outlier ? "outlier" : t.status}
                    </span>
                  </td>
                </tr>
              ))}
              {trades.length === 0 && (
                <tr><td colSpan={6} className="py-6 text-center text-muted">No trades recorded.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
