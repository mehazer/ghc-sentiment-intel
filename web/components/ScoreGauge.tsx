export function ScoreGauge({ score, label }: { score: number; label: string }) {
  const clamped = Math.max(0, Math.min(100, score));
  const angle = (clamped / 100) * 180;
  const color = clamped >= 71 ? "#16c784" : clamped >= 51 ? "#f0b90b" : clamped >= 26 ? "#7c8798" : "#ea3943";
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 110" className="w-full max-w-[220px]">
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="#1b2331" strokeWidth="14" strokeLinecap="round" />
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={`${(angle / 180) * 251} 251`} />
        <text x="100" y="86" textAnchor="middle" className="fill-white" style={{ fontSize: 30, fontWeight: 700, fontFamily: "ui-monospace" }}>
          {clamped.toFixed(0)}
        </text>
      </svg>
      <div className="mt-1 text-center text-xs text-muted">{label}</div>
    </div>
  );
}
