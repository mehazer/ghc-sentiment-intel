import { api, fmt } from "@/lib/api";

export const dynamic = "force-dynamic";

const NARRATIVES = [
  "ETF", "AI tokens", "Layer 2", "Restaking", "RWA", "Meme coins", "GameFi",
  "Token unlock", "Exchange hack", "Whale accumulation", "Adoption", "Regulation",
];

export default async function Narratives() {
  const ranking = await api.ranking();
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white">Narratives</h1>
        <p className="text-sm text-muted">Themes detected by keyword and topic-model clustering across ingested posts.</p>
      </header>
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {NARRATIVES.map((name) => {
          const related = ranking.filter((r) => r.explanation?.primary_driver?.includes(name.toLowerCase().split(" ")[0]));
          return (
            <div key={name} className="card">
              <div className="flex items-center justify-between">
                <span className="text-sm text-white">{name}</span>
                <span className="pill bg-edge text-muted">{related.length} assets</span>
              </div>
              <div className="mt-3 space-y-1 text-xs text-muted">
                {related.slice(0, 3).map((r) => (
                  <div key={r.asset} className="flex justify-between">
                    <span className="font-mono text-slate-300">{r.asset}</span>
                    <span>{fmt(r.alpha_score, 0)}</span>
                  </div>
                ))}
                {related.length === 0 && <span>No active assets.</span>}
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
}
