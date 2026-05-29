import { api } from "@/services/api";
import type {
  Application,
  ApplicationStatus,
  Candidate,
  CandidateNote,
  CandidateTimelineItem,
  PaginatedResponse,
  ResumeAnalysis,
  ScreeningResult,
  SuccessResponse,
} from "@/types/api";

export interface CreateCandidatePayload {
  full_name: string;
  email: string;
  phone?: string;
  job_id?: string;
}

export interface ApplicationListFilters {
  job_id?: string;
  status?: string;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export async function listCandidates(
  search?: string,
  page = 1,
  pageSize = 20,
): Promise<PaginatedResponse<Candidate>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<Candidate>>>("/candidates", {
    params: { search, page, page_size: pageSize },
  });
  return data.data;
}

export async function getCandidate(id: string): Promise<Candidate> {
  const { data } = await api.get<SuccessResponse<Candidate>>(`/candidates/${id}`);
  return data.data;
}

export async function createCandidate(payload: CreateCandidatePayload): Promise<Candidate> {
  const { data } = await api.post<SuccessResponse<Candidate>>("/candidates", payload);
  return data.data;
}

export async function uploadResume(
  candidateId: string,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<{ resume_file_id: string; file_url: string; file_name: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<
    SuccessResponse<{ resume_file_id: string; file_url: string; file_name: string }>
  >(`/candidates/${candidateId}/resume`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (!event.total || !onProgress) return;
      onProgress(Math.round((event.loaded / event.total) * 100));
    },
  });
  return data.data;
}

export async function analyzeCandidate(
  candidateId: string,
  jobId: string,
): Promise<ScreeningResult> {
  const { data } = await api.post<SuccessResponse<ScreeningResult>>(
    `/candidates/${candidateId}/analyze`,
    null,
    { params: { job_id: jobId } },
  );
  return data.data;
}

export async function getCandidateAnalysis(candidateId: string): Promise<ResumeAnalysis> {
  const { data } = await api.get<SuccessResponse<ResumeAnalysis>>(
    `/candidates/${candidateId}/analysis`,
  );
  return data.data;
}

export async function listCandidateNotes(candidateId: string): Promise<CandidateNote[]> {
  const { data } = await api.get<SuccessResponse<{ items: CandidateNote[] }>>(
    `/candidates/${candidateId}/notes`,
  );
  return data.data.items;
}

export async function createCandidateNote(
  candidateId: string,
  note: string,
): Promise<CandidateNote> {
  const { data } = await api.post<SuccessResponse<CandidateNote>>(
    `/candidates/${candidateId}/notes`,
    { note },
  );
  return data.data;
}

export async function listApplications(
  filters: ApplicationListFilters = {},
): Promise<PaginatedResponse<Application>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<Application>>>(
    "/applications",
    { params: filters },
  );
  return data.data;
}

export async function getApplication(id: string): Promise<Application> {
  const { data } = await api.get<SuccessResponse<Application>>(`/applications/${id}`);
  return data.data;
}

export async function updateApplicationStatus(
  applicationId: string,
  status: ApplicationStatus,
  remarks?: string,
): Promise<Application> {
  const { data } = await api.patch<SuccessResponse<Application>>(
    `/applications/${applicationId}/status`,
    { status, remarks },
  );
  return data.data;
}

export async function shortlistApplication(applicationId: string): Promise<Application> {
  const { data } = await api.post<SuccessResponse<Application>>(
    `/applications/${applicationId}/shortlist`,
  );
  return data.data;
}

export async function rejectApplication(applicationId: string): Promise<Application> {
  const { data } = await api.post<SuccessResponse<Application>>(
    `/applications/${applicationId}/reject`,
  );
  return data.data;
}

export async function overrideAI(
  applicationId: string,
  status: ApplicationStatus,
  remarks?: string,
): Promise<Application> {
  const { data } = await api.post<SuccessResponse<Application>>(
    `/candidates/${applicationId}/override`,
    { status, remarks },
  );
  return data.data;
}

export async function getApplicationTimeline(
  applicationId: string,
): Promise<CandidateTimelineItem[]> {
  const { data } = await api.get<
    SuccessResponse<{ application_id: string; items: CandidateTimelineItem[] }>
  >(`/applications/${applicationId}/timeline`);
  return data.data.items;
}

export async function screenApplication(applicationId: string): Promise<ScreeningResult> {
  const { data } = await api.post<SuccessResponse<ScreeningResult>>(
    `/applications/${applicationId}/screen`,
  );
  return data.data;
}

export async function bulkShortlistApplications(applicationIds: string[]): Promise<void> {
  await Promise.all(applicationIds.map((id) => shortlistApplication(id)));
}
