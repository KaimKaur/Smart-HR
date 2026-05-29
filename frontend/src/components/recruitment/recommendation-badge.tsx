import { cn } from "@/lib/utils";

const recommendationTone: Record<string, string> = {
  shortlist: "bg-green-100 text-green-800",
  review: "bg-yellow-100 text-yellow-800",
  reject: "bg-red-100 text-red-800",
};

export function RecommendationBadge({ recommendation }: { recommendation?: string | null }) {
  if (!recommendation) return <span className="text-xs text-muted-foreground">—</span>;
  const key = recommendation.toLowerCase();
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        recommendationTone[key] ?? "bg-blue-100 text-blue-800",
      )}
    >
      {recommendation}
    </span>
  );
}
