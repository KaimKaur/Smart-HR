import { cn } from "@/lib/utils";

export function StarRating({
  rating,
  max = 5,
  size = "md",
}: {
  rating: number;
  max?: number;
  size?: "sm" | "md";
}) {
  const starSize = size === "sm" ? "text-sm" : "text-lg";
  return (
    <div className={cn("flex items-center gap-0.5", starSize)} aria-label={`Rating ${rating} out of ${max}`}>
      {Array.from({ length: max }, (_, index) => {
        const value = index + 1;
        const filled = rating >= value;
        const half = !filled && rating >= value - 0.5;
        return (
          <span
            key={value}
            className={cn(
              filled ? "text-yellow-500" : half ? "text-yellow-300" : "text-muted-foreground/40",
            )}
          >
            ★
          </span>
        );
      })}
      <span className="ml-1 text-xs text-muted-foreground">{rating.toFixed(1)}</span>
    </div>
  );
}
