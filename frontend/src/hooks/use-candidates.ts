"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import { jobKeys } from "@/hooks/use-jobs";
import {
  analyzeCandidate,
  createCandidate,
  createCandidateNote,
  getApplication,
  getApplicationTimeline,
  getCandidate,
  getCandidateAnalysis,
  listApplications,
  listCandidateNotes,
  overrideAI,
  rejectApplication,
  shortlistApplication,
  updateApplicationStatus,
  type ApplicationListFilters,
  type CreateCandidatePayload,
} from "@/services/candidate.service";
import { listJobCandidates } from "@/services/job.service";
import type { ApplicationStatus } from "@/types/api";

export const candidateKeys = {
  all: ["candidates"] as const,
  details: () => [...candidateKeys.all, "detail"] as const,
  detail: (id: string) => [...candidateKeys.details(), id] as const,
  notes: (id: string) => [...candidateKeys.all, "notes", id] as const,
  analysis: (id: string) => [...candidateKeys.all, "analysis", id] as const,
  timeline: (applicationId: string) => [...candidateKeys.all, "timeline", applicationId] as const,
  applications: (filters: ApplicationListFilters) =>
    [...candidateKeys.all, "applications", filters] as const,
};

export function useCandidate(id: string | undefined) {
  return useApiQuery({
    queryKey: candidateKeys.detail(id ?? ""),
    queryFn: () => getCandidate(id!),
    enabled: Boolean(id),
  });
}

export function useCandidates(jobId: string | undefined, filters: ApplicationListFilters = {}) {
  return useApiQuery({
    queryKey: jobKeys.candidates(jobId ?? "", {
      status: filters.status,
      sort_by: filters.sort_by ?? "ai_score",
      sort_order: filters.sort_order ?? "desc",
      page: filters.page,
      page_size: filters.page_size,
    }),
    queryFn: () =>
      listJobCandidates(jobId!, {
        status: filters.status,
        sort_by: filters.sort_by ?? "ai_score",
        sort_order: filters.sort_order ?? "desc",
        page: filters.page,
        page_size: filters.page_size,
      }),
    enabled: Boolean(jobId),
  });
}

export function useCandidateNotes(candidateId: string | undefined) {
  return useApiQuery({
    queryKey: candidateKeys.notes(candidateId ?? ""),
    queryFn: () => listCandidateNotes(candidateId!),
    enabled: Boolean(candidateId),
  });
}

export function useCandidateAnalysis(candidateId: string | undefined) {
  return useApiQuery({
    queryKey: candidateKeys.analysis(candidateId ?? ""),
    queryFn: () => getCandidateAnalysis(candidateId!),
    enabled: Boolean(candidateId),
    retry: false,
  });
}

export function useApplicationTimeline(applicationId: string | undefined) {
  return useApiQuery({
    queryKey: candidateKeys.timeline(applicationId ?? ""),
    queryFn: () => getApplicationTimeline(applicationId!),
    enabled: Boolean(applicationId),
  });
}

export function useCreateCandidate() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: CreateCandidatePayload) => createCandidate(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: candidateKeys.all });
      await queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
    },
  });
}

export function useCreateCandidateNote(candidateId: string) {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (note: string) => createCandidateNote(candidateId, note),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: candidateKeys.notes(candidateId) });
    },
  });
}

export function useShortlistCandidate() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (applicationId: string) => shortlistApplication(applicationId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: jobKeys.all });
      await queryClient.invalidateQueries({ queryKey: candidateKeys.all });
    },
  });
}

export function useRejectCandidate() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (applicationId: string) => rejectApplication(applicationId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: jobKeys.all });
      await queryClient.invalidateQueries({ queryKey: candidateKeys.all });
    },
  });
}

export function useUpdateCandidateStatus() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({
      applicationId,
      status,
      remarks,
    }: {
      applicationId: string;
      status: ApplicationStatus;
      remarks?: string;
    }) => updateApplicationStatus(applicationId, status, remarks),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: jobKeys.all });
      await queryClient.invalidateQueries({ queryKey: candidateKeys.all });
    },
  });
}

export function useOverrideAI() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({
      applicationId,
      status,
      remarks,
    }: {
      applicationId: string;
      status: ApplicationStatus;
      remarks?: string;
    }) => overrideAI(applicationId, status, remarks),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: jobKeys.all });
      await queryClient.invalidateQueries({ queryKey: candidateKeys.all });
    },
  });
}

export function useAnalyzeCandidate() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({ candidateId, jobId }: { candidateId: string; jobId: string }) =>
      analyzeCandidate(candidateId, jobId),
    onSuccess: async (_data, { candidateId }) => {
      await queryClient.invalidateQueries({ queryKey: candidateKeys.analysis(candidateId) });
      await queryClient.invalidateQueries({ queryKey: jobKeys.all });
    },
  });
}

export function useApplication(applicationId: string | undefined) {
  return useApiQuery({
    queryKey: [...candidateKeys.all, "application", applicationId],
    queryFn: () => getApplication(applicationId!),
    enabled: Boolean(applicationId),
  });
}

export function useApplications(filters: ApplicationListFilters = {}) {
  return useApiQuery({
    queryKey: candidateKeys.applications(filters),
    queryFn: () => listApplications(filters),
  });
}
