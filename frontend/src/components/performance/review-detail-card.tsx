"use client";

import { useState } from "react";

import { PerformanceFeedbackForm } from "@/components/performance/performance-feedback-form";
import { StarRating } from "@/components/performance/star-rating";
import type { EmployeePerformanceSummary } from "@/types/api";

export function ReviewDetailCard({ review }: { review: EmployeePerformanceSummary }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="rounded-xl border bg-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">{review.cycle.name}</h3>
          <p className="text-sm text-muted-foreground">
            Reviewer: {review.reviewer.full_name} · {review.cycle.start_date} to {review.cycle.end_date}
          </p>
        </div>
        <StarRating rating={review.rating} />
      </div>

      <button
        type="button"
        className="mt-3 text-sm text-primary hover:underline"
        onClick={() => setExpanded((value) => !value)}
      >
        {expanded ? "Hide details" : "Show scores and feedback"}
      </button>

      {expanded ? (
        <div className="mt-4 space-y-4">
          <div className="space-y-2">
            <p className="text-sm font-medium">Metric scores</p>
            {review.metric_scores.length ? (
              review.metric_scores.map((score) => (
                <div key={score.id} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{score.metric_name}</span>
                    <span>{score.score.toFixed(0)}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted">
                    <div
                      className="h-2 rounded-full bg-primary"
                      style={{ width: `${Math.min(100, Math.max(0, score.score))}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No metric scores recorded.</p>
            )}
          </div>
          <PerformanceFeedbackForm reviewId={review.review_id} />
        </div>
      ) : null}
    </article>
  );
}
