"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import {
  listInterviews,
  scheduleInterview,
  updateInterview,
  type InterviewListFilters,
  type ScheduleInterviewPayload,
  type UpdateInterviewPayload,
} from "@/services/interview.service";

export const interviewKeys = {
  all: ["interviews"] as const,
  list: (filters: InterviewListFilters) => [...interviewKeys.all, "list", filters] as const,
};

export function useInterviews(filters: InterviewListFilters = {}) {
  return useApiQuery({
    queryKey: interviewKeys.list(filters),
    queryFn: () => listInterviews(filters),
  });
}

export function useScheduleInterview() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: ScheduleInterviewPayload) => scheduleInterview(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: interviewKeys.all });
    },
  });
}

export function useUpdateInterview() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateInterviewPayload }) =>
      updateInterview(id, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: interviewKeys.all });
    },
  });
}
