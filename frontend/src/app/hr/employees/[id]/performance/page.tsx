'use client'

"use client";

import { useParams } from "next/navigation";
import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { LoadingSpinner } from "@/components/common/loading-spinner";
import { PageHeader } from "@/components/common/page-header";
import { ReviewDetailCard } from "@/components/performance/review-detail-card";
import { useEmployee } from "@/hooks/use-employees";
import { useReviews } from "@/hooks/use-performance";

export default function EmployeePerformanceHistoryPage() {
  const params = useParams<{ id: string }>();
  const employeeId = params.id;
  const employeeQuery = useEmployee(employeeId);
  const reviewsQuery = useReviews(employeeId, 1, 50);

  const trendData = useMemo(() => {
    const items = [...(reviewsQuery.data?.items ?? [])].sort(
      (a, b) => new Date(a.cycle.start_date).getTime() - new Date(b.cycle.start_date).getTime(),
    );
    return items.map((item) => ({
      cycle: item.cycle.name,
      rating: item.rating,
    }));
  }, [reviewsQuery.data?.items]);

  if (employeeQuery.isLoading || reviewsQuery.isLoading) {
    return <LoadingSpinner label="Loading performance history..." />;
  }

  const employee = employeeQuery.data;
  const reviews = reviewsQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={employee ? `${employee.full_name} — Performance` : "Employee performance"}
        description="Timeline of reviews, rating trend, and detailed scores."
      />

      {trendData.length > 1 ? (
        <section className="rounded-xl border bg-card p-4">
          <h2 className="mb-4 text-base font-semibold">Average rating trend</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="cycle" />
                <YAxis domain={[0, 5]} />
                <Tooltip />
                <Line type="monotone" dataKey="rating" stroke="#2563eb" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      ) : null}

      <section className="space-y-4">
        <h2 className="text-base font-semibold">Review timeline</h2>
        {!reviews.length ? (
          <p className="text-sm text-muted-foreground">No performance reviews found.</p>
        ) : (
          reviews.map((review) => <ReviewDetailCard key={review.review_id} review={review} />)
        )}
      </section>
    </div>
  );
}
