"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmployeeSearch } from "@/components/employees/employee-search";
import { FormField } from "@/components/common/form-field";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { useCreateReview, useCycles, useMetrics, useAddMetricScore } from "@/hooks/use-performance";
import { useToast } from "@/hooks/use-toast";
import { performanceReviewSchema } from "@/lib/validations";

type ReviewFormValues = z.infer<typeof performanceReviewSchema>;

export default function NewPerformanceReviewPage() {
  const router = useRouter();
  const toast = useToast();
  const cyclesQuery = useCycles(1, 100);
  const metricsQuery = useMetrics(1, 100);
  const createReviewMutation = useCreateReview();
  const addScoreMutation = useAddMetricScore();
  const [metricScores, setMetricScores] = useState<Record<string, number>>({});

  const form = useForm<ReviewFormValues>({
    resolver: zodResolver(performanceReviewSchema),
    defaultValues: {
      cycle_id: "",
      employee_id: "",
      rating: 3,
      comments: "",
    },
  });

  const rating = form.watch("rating");

  return (
    <div className="space-y-6">
      <PageHeader title="Create performance review" description="Record ratings, comments, and metric scores." />

      <form
        className="space-y-4 rounded-xl border bg-card p-4"
        onSubmit={form.handleSubmit(async (values) => {
          const review = await createReviewMutation.mutateAsync(values);
          await Promise.all(
            Object.entries(metricScores).map(([metricId, score]) =>
              addScoreMutation.mutateAsync({
                reviewId: review.id,
                payload: { metric_id: metricId, score },
              }),
            ),
          );
          toast.success("Performance review created.");
          router.push("/hr/performance/cycles");
        })}
      >
        <FormField label="Cycle" required error={form.formState.errors.cycle_id?.message}>
          <select className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("cycle_id")}>
            <option value="">Select cycle</option>
            {(cyclesQuery.data?.items ?? []).map((cycle) => (
              <option key={cycle.id} value={cycle.id}>
                {cycle.name} ({cycle.start_date} – {cycle.end_date})
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Employee" required error={form.formState.errors.employee_id?.message}>
          <EmployeeSearch
            value={form.watch("employee_id") || null}
            onChange={(id) => form.setValue("employee_id", id ?? "", { shouldValidate: true })}
          />
        </FormField>

        <FormField label="Rating (1–5)" required error={form.formState.errors.rating?.message}>
          <div className="space-y-2">
            <input
              type="range"
              min={1}
              max={5}
              step={0.5}
              className="w-full"
              {...form.register("rating", { valueAsNumber: true })}
            />
            <p className="text-sm text-muted-foreground">Selected: {rating.toFixed(1)} / 5</p>
            <div className="flex gap-1 text-yellow-500">
              {Array.from({ length: 5 }, (_, i) => (
                <button
                  key={i}
                  type="button"
                  className={rating >= i + 1 ? "opacity-100" : rating >= i + 0.5 ? "opacity-60" : "opacity-30"}
                  onClick={() => form.setValue("rating", i + 1, { shouldValidate: true })}
                >
                  ★
                </button>
              ))}
            </div>
          </div>
        </FormField>

        <FormField label="Comments" error={form.formState.errors.comments?.message}>
          <textarea rows={4} className="w-full rounded-lg border px-3 py-2 text-sm" {...form.register("comments")} />
        </FormField>

        <div className="space-y-3">
          <p className="text-sm font-medium">Metric scores (0–100)</p>
          {(metricsQuery.data?.items ?? []).map((metric) => (
            <label key={metric.id} className="grid gap-1 text-sm sm:grid-cols-2 sm:items-center">
              <span>{metric.name}</span>
              <input
                type="number"
                min={0}
                max={100}
                className="h-9 rounded-lg border px-3"
                value={metricScores[metric.id] ?? ""}
                onChange={(event) => {
                  const value = Number(event.target.value);
                  setMetricScores((current) => ({
                    ...current,
                    [metric.id]: Number.isNaN(value) ? 0 : value,
                  }));
                }}
              />
            </label>
          ))}
        </div>

        <Button type="submit" disabled={createReviewMutation.isPending}>
          {createReviewMutation.isPending ? "Saving..." : "Create review"}
        </Button>
      </form>
    </div>
  );
}
