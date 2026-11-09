"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, LineStyle } from "lightweight-charts";

export function Sparkline({ points, height = 220 }: { points: { time: string; value: number }[]; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || points.length === 0) return;
    const chart = createChart(ref.current, {
      height,
      layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: "#7c8798" },
      grid: { vertLines: { color: "#131a24" }, horzLines: { color: "#131a24" } },
      rightPriceScale: { borderColor: "#1b2331" },
      timeScale: { borderColor: "#1b2331", timeVisible: true },
      crosshair: { mode: 1 },
    });
    const series = chart.addAreaSeries({
      lineColor: "#16c784",
      topColor: "rgba(22,199,132,0.35)",
      bottomColor: "rgba(22,199,132,0.02)",
      lineWidth: 2,
      priceLineStyle: LineStyle.Dotted,
    });
    series.setData(points.map((p) => ({ time: p.time.slice(0, 19), value: p.value })));
    chart.timeScale().fitContent();
    const onResize = () => chart.applyOptions({ width: ref.current?.clientWidth ?? 600 });
    onResize();
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); chart.remove(); };
  }, [points, height]);

  if (points.length === 0) {
    return <div className="flex h-[220px] items-center justify-center text-sm text-muted">No history yet</div>;
  }
  return <div ref={ref} className="w-full" />;
}
