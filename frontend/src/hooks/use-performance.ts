"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import {
  addFeedback,
  addMetricScore,
  createCycle,
  createMetric,
  createReview,
  deleteMetric,
  listCycles,
  listEmployeePerformanceHistory,
  listFeedback,
  listMetricScores,
  listMetrics,
  listMyReviews,
  listTeamPerformance,
  updateMetric,
  type CreateCyclePayload,
  type CreateReviewPayload,
  type FeedbackPayload,
  type MetricScorePayload,
  type PerformanceMetricPayload,
} from "@/services/performance.service";

export const performanceKeys = {
  all: ["performance"] as const,
  cycles: (page: number, pageSize: number) => [...performanceKeys.all, "cycles", page, pageSize] as const,
  cycle: (id: string) => [...performanceKeys.all, "cycle", id] as const,
  reviews: (employeeId: string, page: number, pageSize: number) =>
    [...performanceKeys.all, "reviews", employeeId, page, pageSize] as const,
  myReviews: (page: number, pageSize: number) =>
    [...performanceKeys.all, "my-reviews", page, pageSize] as const,
  team: (cycleId: string | undefined, page: number, pageSize: number) =>
    [...performanceKeys.all, "team", cycleId ?? "all", page, pageSize] as const,
  metrics: (page: number, pageSize: number) =>
    [...performanceKeys.all, "metrics", page, pageSize] as const,
  scores: (reviewId: string) => [...performanceKeys.all, "scores", reviewId] as const,
  feedback: (reviewId: string) => [...performanceKeys.all, "feedback", reviewId] as const,
};

export function useCycles(page = 1, pageSize = 20) {
  return useApiQuery({
    queryKey: performanceKeys.cycles(page, pageSize),
    queryFn: () => listCycles(page, pageSize),
  });
}

export function useReviews(employeeId: string | undefined, page = 1, pageSize = 20) {
  return useApiQuery({
    queryKey: performanceKeys.reviews(employeeId ?? "", page, pageSize),
    queryFn: () => listEmployeePerformanceHistory(employeeId!, page, pageSize),
    enabled: Boolean(employeeId),
  });
}

export function useCreateReview() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: CreateReviewPayload) => createReview(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: performanceKeys.all });
    },
  });
}

export function useMetrics(page = 1, pageSize = 100) {
  return useApiQuery({
    queryKey: performanceKeys.metrics(page, pageSize),
    queryFn: () => listMetrics(page, pageSize),
  });
}

export function useMetricScores(reviewId: string | undefined) {
  return useApiQuery({
    queryKey: performanceKeys.scores(reviewId ?? ""),
    queryFn: () => listMetricScores(reviewId!),
    enabled: Boolean(reviewId),
  });
}

export function useFeedback(reviewId: string | undefined) {
  return useApiQuery({
    queryKey: performanceKeys.feedback(reviewId ?? ""),
    queryFn: () => listFeedback(reviewId!),
    enabled: Boolean(reviewId),
  });
}

export function useMyReviews(page = 1, pageSize = 20) {
  return useApiQuery({
    queryKey: performanceKeys.myReviews(page, pageSize),
    queryFn: () => listMyReviews(page, pageSize),
  });
}

export function useTeamPerformance(cycleId?: string, page = 1, pageSize = 20) {
  return useApiQuery({
    queryKey: performanceKeys.team(cycleId, page, pageSize),
    queryFn: () => listTeamPerformance(cycleId, page, pageSize),
  });
}

export function useCreateCycle() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: CreateCyclePayload) => createCycle(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: performanceKeys.all });
    },
  });
}

export function useCreateMetric() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: PerformanceMetricPayload) => createMetric(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: performanceKeys.all });
    },
  });
}

export function useUpdateMetric() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({ metricId, payload }: { metricId: string; payload: PerformanceMetricPayload }) =>
      updateMetric(metricId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: performanceKeys.all });
    },
  });
}

export function useDeleteMetric() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (metricId: string) => deleteMetric(metricId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: performanceKeys.all });
    },
  });
}

export function useAddMetricScore() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({
      reviewId,
      payload,
    }: {
      reviewId: string;
      payload: MetricScorePayload;
    }) => addMetricScore(reviewId, payload),
    onSuccess: async (_data, { reviewId }) => {
      await queryClient.invalidateQueries({ queryKey: performanceKeys.scores(reviewId) });
      await queryClient.invalidateQueries({ queryKey: performanceKeys.all });
    },
  });
}

export function useAddFeedback() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({ reviewId, payload }: { reviewId: string; payload: FeedbackPayload }) =>
      addFeedback(reviewId, payload),
    onSuccess: async (_data, { reviewId }) => {
      await queryClient.invalidateQueries({ queryKey: performanceKeys.feedback(reviewId) });
      await queryClient.invalidateQueries({ queryKey: performanceKeys.all });
    },
  });
}
