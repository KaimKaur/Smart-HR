import { api } from "@/services/api";
import type { Job, JobCandidateRow, PaginatedResponse, SuccessResponse } from "@/types/api";

export interface JobListFilters {
  status?: string;
  department_id?: string;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export interface CreateJobPayload {
  title: string;
  department_id?: string;
  description: string;
  skills: string[];
}

export type UpdateJobPayload = Partial<CreateJobPayload>;

export async function listJobs(filters: JobListFilters = {}): Promise<PaginatedResponse<Job>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<Job>>>("/jobs", {
    params: filters,
  });
  return data.data;
}

export async function getJob(id: string): Promise<Job> {
  const { data } = await api.get<SuccessResponse<Job>>(`/jobs/${id}`);
  return data.data;
}

export async function createJob(payload: CreateJobPayload): Promise<Job> {
  const { data } = await api.post<SuccessResponse<Job>>("/jobs", payload);
  return data.data;
}

export async function updateJob(id: string, payload: UpdateJobPayload): Promise<Job> {
  const { data } = await api.patch<SuccessResponse<Job>>(`/jobs/${id}`, payload);
  return data.data;
}

export async function deleteJob(id: string): Promise<void> {
  await api.delete(`/jobs/${id}`);
}

export async function publishJob(id: string): Promise<Job> {
  const { data } = await api.post<SuccessResponse<Job>>(`/jobs/${id}/publish`);
  return data.data;
}

export async function closeJob(id: string): Promise<Job> {
  const { data } = await api.post<SuccessResponse<Job>>(`/jobs/${id}/close`);
  return data.data;
}

export interface JobCandidateFilters {
  status?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export async function listJobCandidates(
  jobId: string,
  filters: JobCandidateFilters = {},
): Promise<PaginatedResponse<JobCandidateRow>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<JobCandidateRow>>>(
    `/jobs/${jobId}/candidates`,
    { params: filters },
  );
  return data.data;
}

export async function getJobCandidateRanking(
  jobId: string,
  page = 1,
  pageSize = 100,
): Promise<PaginatedResponse<JobCandidateRow>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<JobCandidateRow>>>(
    `/jobs/${jobId}/candidates/ranking`,
    { params: { page, page_size: pageSize } },
  );
  return data.data;
}

export async function getApplicationCount(jobId: string): Promise<number> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<JobCandidateRow>>>(
    `/jobs/${jobId}/candidates`,
    { params: { page: 1, page_size: 1 } },
  );
  return data.data.pagination.total_items;
}
