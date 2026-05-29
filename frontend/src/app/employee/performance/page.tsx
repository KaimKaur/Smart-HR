"use client";

import { PageHeader } from "@/components/common/page-header";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { ReviewDetailCard } from "@/components/performance/review-detail-card";
import { useMyReviews } from "@/hooks/use-performance";

export default function EmployeePerformancePage() {
  const reviewsQuery = useMyReviews(1, 50);

  if (reviewsQuery.isLoading) {
    return <LoadingSpinner label="Loading performance reviews..." />;
  }

  const reviews = reviewsQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="My performance"
        description="Review history across performance cycles."
      />

      {!reviews.length ? (
        <p className="text-sm text-muted-foreground">No performance reviews yet.</p>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <ReviewDetailCard key={review.review_id} review={review} />
          ))}
        </div>
      )}
    </div>
  );
}
