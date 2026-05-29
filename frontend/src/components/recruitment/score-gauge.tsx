export function ScoreGauge({ score }: { score: number }) {
  const normalized = Math.max(0, Math.min(100, score));
  const degrees = (normalized / 100) * 360;

  return (
    <div className="relative inline-flex h-24 w-24 items-center justify-center">
      <div
        className="absolute inset-0 rounded-full bg-muted"
        style={{
          background: `conic-gradient(#111 ${degrees}deg, #e5e7eb ${degrees}deg)`,
        }}
      />
      <div className="absolute inset-2 flex items-center justify-center rounded-full bg-background text-lg font-semibold">
        {Math.round(normalized)}
      </div>
    </div>
  );
}
