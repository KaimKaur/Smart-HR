import { api } from "@/services/api";
import type { Interview, PaginatedResponse, SuccessResponse } from "@/types/api";

export interface InterviewListFilters {
  application_id?: string;
  interviewer_id?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export interface ScheduleInterviewPayload {
  application_id: string;
  scheduled_at: string;
  interviewer_id?: string;
  notes?: string;
}

export interface UpdateInterviewPayload {
  scheduled_at?: string;
  interviewer_id?: string;
  status?: "scheduled" | "completed" | "cancelled" | "no_show";
  notes?: string;
}

export async function listInterviews(
  filters: InterviewListFilters = {},
): Promise<PaginatedResponse<Interview>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<Interview>>>("/interviews", {
    params: filters,
  });
  return data.data;
}

export async function getInterview(id: string): Promise<Interview> {
  const { data } = await api.get<SuccessResponse<Interview>>(`/interviews/${id}`);
  return data.data;
}

export async function scheduleInterview(payload: ScheduleInterviewPayload): Promise<Interview> {
  const { data } = await api.post<SuccessResponse<Interview>>("/interviews", payload);
  return data.data;
}

export async function updateInterview(
  id: string,
  payload: UpdateInterviewPayload,
): Promise<Interview> {
  const { data } = await api.patch<SuccessResponse<Interview>>(`/interviews/${id}`, payload);
  return data.data;
}
