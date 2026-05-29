import { api } from "@/services/api";
import type {
  AttendanceStatus,
  Department,
  Designation,
  EmploymentStatus,
  PaginatedResponse,
  SuccessResponse,
} from "@/types/api";

export interface CreateDepartmentPayload {
  name: string;
  description?: string;
}

export interface UpdateDepartmentPayload {
  name?: string;
  description?: string;
}

export interface CreateDesignationPayload {
  title: string;
  description?: string;
}

export interface UpdateDesignationPayload {
  title?: string;
  description?: string;
}

export async function listDepartments(
  page = 1,
  pageSize = 100,
): Promise<PaginatedResponse<Department>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<Department>>>(
    "/departments",
    { params: { page, page_size: pageSize } },
  );
  return data.data;
}

export async function createDepartment(payload: CreateDepartmentPayload): Promise<Department> {
  const { data } = await api.post<SuccessResponse<Department>>("/departments", payload);
  return data.data;
}

export async function updateDepartment(
  id: string,
  payload: UpdateDepartmentPayload,
): Promise<Department> {
  const { data } = await api.patch<SuccessResponse<Department>>(`/departments/${id}`, payload);
  return data.data;
}

export async function deleteDepartment(id: string): Promise<void> {
  await api.delete(`/departments/${id}`);
}

export async function listDesignations(
  page = 1,
  pageSize = 100,
): Promise<PaginatedResponse<Designation>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<Designation>>>(
    "/designations",
    { params: { page, page_size: pageSize } },
  );
  return data.data;
}

export async function createDesignation(payload: CreateDesignationPayload): Promise<Designation> {
  const { data } = await api.post<SuccessResponse<Designation>>("/designations", payload);
  return data.data;
}

export async function updateDesignation(
  id: string,
  payload: UpdateDesignationPayload,
): Promise<Designation> {
  const { data } = await api.patch<SuccessResponse<Designation>>(`/designations/${id}`, payload);
  return data.data;
}

export async function deleteDesignation(id: string): Promise<void> {
  await api.delete(`/designations/${id}`);
}

export async function listEmploymentStatuses(): Promise<EmploymentStatus[]> {
  const { data } = await api.get<SuccessResponse<{ items: EmploymentStatus[] }>>(
    "/employment-statuses",
  );
  return data.data.items;
}

export async function listAttendanceStatuses(): Promise<AttendanceStatus[]> {
  const { data } = await api.get<SuccessResponse<{ items: AttendanceStatus[] }>>(
    "/attendance-statuses",
  );
  return data.data.items;
}
