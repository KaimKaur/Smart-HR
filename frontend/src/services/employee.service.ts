import { api } from "@/services/api";
import type {
  Employee,
  EmployeeSearchItem,
  PaginatedResponse,
  SuccessResponse,
} from "@/types/api";

export interface EmployeeListFilters {
  search?: string;
  department_id?: string;
  designation_id?: string;
  status?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export interface CreateEmployeePayload {
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  department_id: string;
  designation_id: string;
  employment_status_id: string;
  manager_id?: string;
  salary?: number;
  join_date: string;
}

export type UpdateEmployeePayload = Partial<CreateEmployeePayload>;

export async function listEmployees(
  filters: EmployeeListFilters = {},
): Promise<PaginatedResponse<Employee>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<Employee>>>("/employees", {
    params: filters,
  });
  return data.data;
}

export async function getEmployee(id: string): Promise<Employee> {
  const { data } = await api.get<SuccessResponse<Employee>>(`/employees/${id}`);
  return data.data;
}

export async function getEmployeeProfile(id: string): Promise<Employee> {
  const { data } = await api.get<SuccessResponse<Employee>>(`/employees/${id}/profile`);
  return data.data;
}

export async function createEmployee(payload: CreateEmployeePayload): Promise<Employee> {
  const { data } = await api.post<SuccessResponse<Employee>>("/employees", payload);
  return data.data;
}

export async function updateEmployee(
  id: string,
  payload: UpdateEmployeePayload,
): Promise<Employee> {
  const { data } = await api.patch<SuccessResponse<Employee>>(`/employees/${id}`, payload);
  return data.data;
}

export async function deactivateEmployee(id: string): Promise<void> {
  await api.delete(`/employees/${id}`);
}

export async function searchEmployees(
  q: string,
  limit = 20,
): Promise<EmployeeSearchItem[]> {
  const { data } = await api.get<SuccessResponse<{ items: EmployeeSearchItem[] }>>(
    "/employees/search",
    { params: { q, limit } },
  );
  return data.data.items;
}
