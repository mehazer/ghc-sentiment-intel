import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "GHC — Sentiment Intelligence",
  description: "Attention, sentiment and smart-money intelligence for Gradual Hedge Cropping.",
};

const nav = [
  { href: "/", label: "Overview" },
  { href: "/ghc", label: "GHC Console" },
  { href: "/narratives", label: "Narratives" },
  { href: "/smart-money", label: "Smart Money" },
  { href: "/alerts", label: "Alerts" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="mx-auto flex min-h-screen max-w-[1500px] gap-6 px-5 py-6">
          <aside className="hidden w-56 shrink-0 flex-col gap-6 lg:flex">
            <div>
              <div className="font-mono text-lg font-bold tracking-tight text-white">GHC</div>
              <div className="text-xs text-muted">Sentiment Intelligence</div>
            </div>
            <nav className="flex flex-col gap-1">
              {nav.map((item) => (
                <Link key={item.href} href={item.href}
                  className="rounded-lg px-3 py-2 text-sm text-slate-300 transition hover:bg-edge hover:text-white">
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="mt-auto text-[11px] leading-relaxed text-muted">
              Signal engine output is probabilistic. Position sizing and risk remain with GHC rules.
            </div>
          </aside>
          <main className="min-w-0 flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
