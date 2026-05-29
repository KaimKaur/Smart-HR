"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import {
  closeJob,
  createJob,
  deleteJob,
  getJob,
  listJobCandidates,
  listJobs,
  publishJob,
  updateJob,
  type CreateJobPayload,
  type JobCandidateFilters,
  type JobListFilters,
  type UpdateJobPayload,
} from "@/services/job.service";

export const jobKeys = {
  all: ["jobs"] as const,
  lists: () => [...jobKeys.all, "list"] as const,
  list: (filters: JobListFilters) => [...jobKeys.lists(), filters] as const,
  details: () => [...jobKeys.all, "detail"] as const,
  detail: (id: string) => [...jobKeys.details(), id] as const,
  candidates: (jobId: string, filters: JobCandidateFilters) =>
    [...jobKeys.all, "candidates", jobId, filters] as const,
};

export function useJobs(filters: JobListFilters = {}) {
  return useApiQuery({
    queryKey: jobKeys.list(filters),
    queryFn: () => listJobs(filters),
  });
}

export function useJob(id: string | undefined) {
  return useApiQuery({
    queryKey: jobKeys.detail(id ?? ""),
    queryFn: () => getJob(id!),
    enabled: Boolean(id),
  });
}

export function useJobCandidates(jobId: string | undefined, filters: JobCandidateFilters = {}) {
  return useApiQuery({
    queryKey: jobKeys.candidates(jobId ?? "", filters),
    queryFn: () => listJobCandidates(jobId!, filters),
    enabled: Boolean(jobId),
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: CreateJobPayload) => createJob(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
    },
  });
}

export function useUpdateJob(id: string) {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: UpdateJobPayload) => updateJob(id, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      await queryClient.invalidateQueries({ queryKey: jobKeys.detail(id) });
    },
  });
}

export function usePublishJob() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (id: string) => publishJob(id),
    onSuccess: async (_data, id) => {
      await queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      await queryClient.invalidateQueries({ queryKey: jobKeys.detail(id) });
    },
  });
}

export function useCloseJob() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (id: string) => closeJob(id),
    onSuccess: async (_data, id) => {
      await queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      await queryClient.invalidateQueries({ queryKey: jobKeys.detail(id) });
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (id: string) => deleteJob(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
    },
  });
}
