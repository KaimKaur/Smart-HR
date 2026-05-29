import { api } from "@/services/api";
import type {
  AttendanceDashboardResponse,
  EmployeeDashboardResponse,
  HRDashboardResponse,
  PerformanceDashboardResponse,
  RecruitmentDashboardResponse,
  SuccessResponse,
} from "@/types/api";

export async function getHRDashboard(): Promise<HRDashboardResponse> {
  const { data } = await api.get<SuccessResponse<HRDashboardResponse>>("/dashboard/hr");
  return data.data;
}

export async function getRecruitmentDashboard(): Promise<RecruitmentDashboardResponse> {
  const { data } = await api.get<SuccessResponse<RecruitmentDashboardResponse>>(
    "/dashboard/recruitment",
  );
  return data.data;
}

export async function getAttendanceDashboard(): Promise<AttendanceDashboardResponse> {
  const { data } = await api.get<SuccessResponse<AttendanceDashboardResponse>>("/dashboard/attendance");
  return data.data;
}

export async function getPerformanceDashboard(): Promise<PerformanceDashboardResponse> {
  const { data } = await api.get<SuccessResponse<PerformanceDashboardResponse>>("/dashboard/performance");
  return data.data;
}

export async function getEmployeeDashboard(): Promise<EmployeeDashboardResponse> {
  const { data } = await api.get<SuccessResponse<EmployeeDashboardResponse>>("/dashboard/employee");
  return data.data;
}

