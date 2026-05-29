import { api } from "@/services/api";
import type {
  AttendanceReportRow,
  EmployeeReportRow,
  PaginatedResponse,
  RecruitmentReportRow,
  SuccessResponse,
} from "@/types/api";

export interface EmployeeReportFilters {
  department_id?: string;
  designation_id?: string;
  employment_status_id?: string;
  date_from?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export async function getEmployeeReport(
  filters: EmployeeReportFilters = {},
): Promise<PaginatedResponse<EmployeeReportRow>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<EmployeeReportRow>>>(
    "/reports/employees",
    { params: filters },
  );
  return data.data;
}

export async function exportEmployeeReport(
  filters: Omit<EmployeeReportFilters, "page" | "page_size"> = {},
): Promise<Blob> {
  const { data } = await api.get<Blob>("/reports/employees/export", {
    params: filters,
    responseType: "blob",
  });
  return data;
}

export interface RecruitmentReportFilters {
  job_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export async function getRecruitmentReport(
  filters: RecruitmentReportFilters = {},
): Promise<PaginatedResponse<RecruitmentReportRow>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<RecruitmentReportRow>>>(
    "/reports/recruitment",
    { params: filters },
  );
  return data.data;
}

export async function exportRecruitmentReport(
  filters: Omit<RecruitmentReportFilters, "page" | "page_size"> = {},
): Promise<Blob> {
  const { data } = await api.get<Blob>("/reports/recruitment/export", {
    params: filters,
    responseType: "blob",
  });
  return data;
}

export interface AttendanceReportFilters {
  employee_id?: string;
  department_id?: string;
  date_from: string;
  date_to: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export async function getAttendanceReport(
  filters: AttendanceReportFilters,
): Promise<PaginatedResponse<AttendanceReportRow>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<AttendanceReportRow>>>(
    "/reports/attendance",
    { params: filters },
  );
  return data.data;
}

export async function exportAttendanceReport(
  filters: Omit<AttendanceReportFilters, "page" | "page_size">,
): Promise<Blob> {
  const { data } = await api.get<Blob>("/reports/attendance/export", {
    params: filters,
    responseType: "blob",
  });
  return data;
}
