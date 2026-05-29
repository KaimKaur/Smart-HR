import { api } from "@/services/api";
import type {
  EmployeePerformanceSummary,
  MetricScore,
  PaginatedResponse,
  PerformanceCycle,
  PerformanceFeedback,
  PerformanceMetric,
  PerformanceReport,
  PerformanceReview,
  SuccessResponse,
} from "@/types/api";

export interface CreateCyclePayload {
  name: string;
  start_date: string;
  end_date: string;
}

export interface CreateReviewPayload {
  cycle_id: string;
  employee_id: string;
  rating: number;
  comments?: string;
}

export interface MetricScorePayload {
  metric_id: string;
  score: number;
}

export interface FeedbackPayload {
  feedback_text: string;
}

export interface PerformanceMetricPayload {
  name: string;
  description?: string;
}

export interface PerformanceReportFilters {
  cycle_id?: string;
  department_id?: string;
  date_from: string;
  date_to: string;
  page?: number;
  page_size?: number;
}

export async function listCycles(
  page = 1,
  pageSize = 20,
): Promise<PaginatedResponse<PerformanceCycle>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<PerformanceCycle>>>(
    "/performance/cycles",
    { params: { page, page_size: pageSize } },
  );
  return data.data;
}

export async function getCycle(cycleId: string): Promise<PerformanceCycle> {
  const { data } = await api.get<SuccessResponse<PerformanceCycle>>(
    `/performance/cycles/${cycleId}`,
  );
  return data.data;
}

export async function createCycle(payload: CreateCyclePayload): Promise<PerformanceCycle> {
  const { data } = await api.post<SuccessResponse<PerformanceCycle>>("/performance/cycles", payload);
  return data.data;
}

export async function createReview(payload: CreateReviewPayload): Promise<PerformanceReview> {
  const { data } = await api.post<SuccessResponse<PerformanceReview>>("/performance/reviews", payload);
  return data.data;
}

export async function listMyReviews(
  page = 1,
  pageSize = 20,
): Promise<PaginatedResponse<EmployeePerformanceSummary>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<EmployeePerformanceSummary>>>(
    "/performance/my-reviews",
    { params: { page, page_size: pageSize } },
  );
  return data.data;
}

export async function listTeamPerformance(
  cycleId?: string,
  page = 1,
  pageSize = 20,
): Promise<PaginatedResponse<EmployeePerformanceSummary>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<EmployeePerformanceSummary>>>(
    "/performance/team",
    {
      params: {
        cycle_id: cycleId,
        page,
        page_size: pageSize,
      },
    },
  );
  return data.data;
}

export async function listEmployeePerformanceHistory(
  employeeId: string,
  page = 1,
  pageSize = 20,
): Promise<PaginatedResponse<EmployeePerformanceSummary>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<EmployeePerformanceSummary>>>(
    `/performance/employees/${employeeId}/history`,
    { params: { page, page_size: pageSize } },
  );
  return data.data;
}

export async function listMetrics(
  page = 1,
  pageSize = 100,
): Promise<PaginatedResponse<PerformanceMetric>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<PerformanceMetric>>>(
    "/performance/metrics",
    { params: { page, page_size: pageSize } },
  );
  return data.data;
}

export async function createMetric(payload: PerformanceMetricPayload): Promise<PerformanceMetric> {
  const { data } = await api.post<SuccessResponse<PerformanceMetric>>("/performance/metrics", payload);
  return data.data;
}

export async function updateMetric(
  metricId: string,
  payload: PerformanceMetricPayload,
): Promise<PerformanceMetric> {
  const { data } = await api.patch<SuccessResponse<PerformanceMetric>>(
    `/performance/metrics/${metricId}`,
    payload,
  );
  return data.data;
}

export async function deleteMetric(metricId: string): Promise<void> {
  await api.delete(`/performance/metrics/${metricId}`);
}

export async function addMetricScore(
  reviewId: string,
  payload: MetricScorePayload,
): Promise<MetricScore> {
  const { data } = await api.post<SuccessResponse<MetricScore>>(
    `/performance/reviews/${reviewId}/scores`,
    payload,
  );
  return data.data;
}

export async function listMetricScores(reviewId: string): Promise<MetricScore[]> {
  const { data } = await api.get<SuccessResponse<MetricScore[]>>(
    `/performance/reviews/${reviewId}/scores`,
  );
  return data.data;
}

export async function addFeedback(
  reviewId: string,
  payload: FeedbackPayload,
): Promise<PerformanceFeedback> {
  const { data } = await api.post<SuccessResponse<PerformanceFeedback>>(
    `/performance/reviews/${reviewId}/feedback`,
    payload,
  );
  return data.data;
}

export async function listFeedback(reviewId: string): Promise<PerformanceFeedback[]> {
  const { data } = await api.get<SuccessResponse<PerformanceFeedback[]>>(
    `/performance/reviews/${reviewId}/feedback`,
  );
  return data.data;
}

export async function getPerformanceReport(
  filters: PerformanceReportFilters,
): Promise<PerformanceReport> {
  const { data } = await api.get<SuccessResponse<PerformanceReport>>("/reports/performance", {
    params: filters,
  });
  return data.data;
}

export async function exportPerformanceReport(
  filters: Omit<PerformanceReportFilters, "page" | "page_size">,
): Promise<Blob> {
  const { data } = await api.get<Blob>("/reports/performance/export", {
    params: filters,
    responseType: "blob",
  });
  return data;
}
