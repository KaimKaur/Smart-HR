import { api } from "@/services/api";
import type {
  InitializeLeaveBalanceResponse,
  LeaveBalanceResponse,
  LeaveRequest,
  LeaveType,
  PaginatedResponse,
  SuccessResponse,
} from "@/types/api";

export interface LeaveHistoryFilters {
  employee_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface LeaveListFilters extends LeaveHistoryFilters {
  leave_type_id?: string;
}

export interface CreateLeaveRequestPayload {
  leave_type_id: string;
  start_date: string;
  end_date: string;
  reason?: string;
}

export interface LeaveApprovalPayload {
  remarks?: string;
}

export interface InitializeLeaveBalancePayload {
  employee_id?: string;
  all_employees: boolean;
}

export interface LeaveTypePayload {
  name: string;
  annual_allocation: number;
}

export interface UpdateLeaveTypePayload {
  name?: string;
  annual_allocation?: number;
}

export async function listLeaveTypes(): Promise<LeaveType[]> {
  const { data } = await api.get<SuccessResponse<{ items: LeaveType[] }>>("/leave-types");
  return data.data.items;
}

export async function listLeaveRequests(
  filters: LeaveListFilters = {},
): Promise<PaginatedResponse<LeaveRequest>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<LeaveRequest>>>("/leave", {
    params: filters,
  });
  return data.data;
}

export async function listLeaveHistory(
  filters: LeaveHistoryFilters = {},
): Promise<PaginatedResponse<LeaveRequest>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<LeaveRequest>>>(
    "/leave/history",
    {
      params: filters,
    },
  );
  return data.data;
}

export async function getLeaveBalance(employeeId?: string): Promise<LeaveBalanceResponse> {
  const endpoint = employeeId ? `/leave/balance/${employeeId}` : "/leave/balance";
  const { data } = await api.get<SuccessResponse<LeaveBalanceResponse>>(endpoint);
  return data.data;
}

export async function getManyLeaveBalances(employeeIds: string[]): Promise<LeaveBalanceResponse[]> {
  return Promise.all(employeeIds.map((employeeId) => getLeaveBalance(employeeId)));
}

export async function createLeaveRequest(
  payload: CreateLeaveRequestPayload,
  employeeId?: string,
): Promise<LeaveRequest> {
  const { data } = await api.post<SuccessResponse<LeaveRequest>>("/leave", payload, {
    params: employeeId ? { employee_id: employeeId } : undefined,
  });
  return data.data;
}

export async function approveLeave(
  leaveRequestId: string,
  payload: LeaveApprovalPayload = {},
): Promise<LeaveRequest> {
  const { data } = await api.post<SuccessResponse<LeaveRequest>>(
    `/leave/${leaveRequestId}/approve`,
    payload,
  );
  return data.data;
}

export async function rejectLeave(
  leaveRequestId: string,
  payload: LeaveApprovalPayload = {},
): Promise<LeaveRequest> {
  const { data } = await api.post<SuccessResponse<LeaveRequest>>(
    `/leave/${leaveRequestId}/reject`,
    payload,
  );
  return data.data;
}

export async function cancelLeave(leaveRequestId: string): Promise<LeaveRequest> {
  const { data } = await api.post<SuccessResponse<LeaveRequest>>(`/leave/${leaveRequestId}/cancel`);
  return data.data;
}

export async function listPendingApprovals(
  page = 1,
  pageSize = 20,
): Promise<PaginatedResponse<LeaveRequest>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<LeaveRequest>>>(
    "/leave/pending-approvals",
    {
      params: { page, page_size: pageSize },
    },
  );
  return data.data;
}

export async function initializeLeaveBalances(
  payload: InitializeLeaveBalancePayload,
): Promise<InitializeLeaveBalanceResponse> {
  const { data } = await api.post<SuccessResponse<InitializeLeaveBalanceResponse>>(
    "/leave/balance/initialize",
    payload,
  );
  return data.data;
}

export async function createLeaveType(payload: LeaveTypePayload): Promise<LeaveType> {
  const { data } = await api.post<SuccessResponse<LeaveType>>("/leave-types", payload);
  return data.data;
}

export async function updateLeaveType(
  leaveTypeId: string,
  payload: UpdateLeaveTypePayload,
): Promise<LeaveType> {
  const { data } = await api.patch<SuccessResponse<LeaveType>>(`/leave-types/${leaveTypeId}`, payload);
  return data.data;
}

export async function deleteLeaveType(leaveTypeId: string): Promise<void> {
  await api.delete(`/leave-types/${leaveTypeId}`);
}
