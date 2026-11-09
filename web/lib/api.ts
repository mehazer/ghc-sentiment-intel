const SERVER_BASE = `${process.env.API_URL ?? "http://localhost:8000"}/api`;
const BROWSER_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api/backend";

/** Server components need an absolute URL; the browser uses the proxy. */
export const API = typeof window === "undefined" ? SERVER_BASE : BROWSER_BASE;

export type Score = {
  asset: string;
  timestamp?: string;
  alpha_score: number;
  sentiment_score: number;
  attention_score: number;
  velocity_score: number;
  smart_money_score: number;
  volume_score: number;
  confidence: number;
  reliability: number;
  classification: string;
  explanation: { summary?: string; primary_driver?: string; components?: Record<string, number> };
};

export type Alert = {
  id: number;
  asset: string;
  kind: string;
  reason: string;
  confidence: number;
  expected_impact: string;
  created_at: string;
};

export type GHCState = {
  balance_line: number;
  deviation_pct: number;
  zone: string;
  daily_pnl_forecast: number;
  csi: number;
  cri_olr: number;
  cri_brc: number;
  updated_at: string;
};

export type Playbook = { zone: string; deviation_pct: number; actions: string[]; guards: string[]; updated_at: string };

export type Trade = {
  id: number;
  basket: string;
  symbol: string;
  side: string;
  size_usd: number;
  entry_price: number;
  deviation_pct: number;
  pnl_usd: number;
  pnl_pct: number;
  status: string;
  is_outlier: boolean;
};

async function get<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${API}${path}`, { cache: "no-store" });
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

export const api = {
  ranking: () => get<Score[]>("/signals/ranking?limit=25", []),
  history: (asset: string) => get<Score[]>(`/signals/${asset}/history?limit=200`, []),
  why: (asset: string) => get<Record<string, unknown>>(`/signals/${asset}/why`, {}),
  alerts: () => get<Alert[]>("/alerts?limit=50", []),
  state: () => get<GHCState | null>("/ghc/state", null),
  playbook: () => get<Playbook | null>("/ghc/playbook", null),
  trades: () => get<Trade[]>("/ghc/trades", []),
  risk: () => get<Record<string, unknown>>("/ghc/risk", {}),
};

export const fmt = (n: number, digits = 1) =>
  Number.isFinite(n) ? n.toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits }) : "—";

export const signed = (n: number, digits = 1) => (n > 0 ? `+${fmt(n, digits)}` : fmt(n, digits));

export const zoneLabel: Record<string, string> = {
  sell_2: "Above S2",
  sell_1: "Between S1–S2",
  between: "Between S1–B1",
  buy_1: "Between B1–B2",
  buy_2: "Below B2",
};
