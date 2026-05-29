import { cn } from "@/lib/utils";

export type StatTrend = "up" | "down" | "neutral";

export function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend = "neutral",
  trendValue,
  isLoading,
}: {
  title: string;
  value?: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: StatTrend;
  trendValue?: string;
  isLoading?: boolean;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {title}
          </p>
          {isLoading ? (
            <div className="mt-2 h-8 w-24 animate-pulse rounded bg-muted" />
          ) : (
            <p className="mt-2 text-2xl font-semibold">{value ?? "—"}</p>
          )}
          {subtitle ? (
            isLoading ? (
              <div className="mt-2 h-4 w-40 animate-pulse rounded bg-muted" />
            ) : (
              <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
            )
          ) : null}
        </div>
        {icon ? <div className="shrink-0 text-muted-foreground">{icon}</div> : null}
      </div>

      {trendValue ? (
        <p
          className={cn(
            "mt-3 text-xs font-medium",
            trend === "up"
              ? "text-green-700"
              : trend === "down"
                ? "text-red-700"
                : "text-muted-foreground",
          )}
        >
          {trend === "up" ? "↑ " : trend === "down" ? "↓ " : "→ "}
          {trendValue}
        </p>
      ) : null}
    </div>
  );
}
