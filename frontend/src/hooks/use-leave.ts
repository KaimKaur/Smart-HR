"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import {
  approveLeave,
  cancelLeave,
  createLeaveRequest,
  createLeaveType,
  deleteLeaveType,
  getLeaveBalance,
  initializeLeaveBalances,
  listLeaveHistory,
  listLeaveRequests,
  listLeaveTypes,
  listPendingApprovals,
  rejectLeave,
  updateLeaveType,
  type CreateLeaveRequestPayload,
  type InitializeLeaveBalancePayload,
  type LeaveHistoryFilters,
  type LeaveListFilters,
  type LeaveTypePayload,
  type UpdateLeaveTypePayload,
} from "@/services/leave.service";

export const leaveKeys = {
  all: ["leave"] as const,
  requests: (filters: LeaveListFilters) => [...leaveKeys.all, "requests", filters] as const,
  history: (filters: LeaveHistoryFilters) => [...leaveKeys.all, "history", filters] as const,
  balances: (employeeId?: string) => [...leaveKeys.all, "balances", employeeId ?? "me"] as const,
  pendingApprovals: (page: number, pageSize: number) =>
    [...leaveKeys.all, "pending-approvals", page, pageSize] as const,
  leaveTypes: () => [...leaveKeys.all, "types"] as const,
};

export function useLeaveRequests(filters: LeaveListFilters = {}) {
  return useApiQuery({
    queryKey: leaveKeys.requests(filters),
    queryFn: () => listLeaveRequests(filters),
  });
}

export function useLeaveHistory(filters: LeaveHistoryFilters = {}) {
  return useApiQuery({
    queryKey: leaveKeys.history(filters),
    queryFn: () => listLeaveHistory(filters),
  });
}

export function useLeaveBalance(employeeId?: string) {
  return useApiQuery({
    queryKey: leaveKeys.balances(employeeId),
    queryFn: () => getLeaveBalance(employeeId),
  });
}

export function usePendingApprovals(page = 1, pageSize = 20) {
  return useApiQuery({
    queryKey: leaveKeys.pendingApprovals(page, pageSize),
    queryFn: () => listPendingApprovals(page, pageSize),
  });
}

export function useLeaveTypes() {
  return useApiQuery({
    queryKey: leaveKeys.leaveTypes(),
    queryFn: listLeaveTypes,
  });
}

export function useCreateLeaveRequest() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({ payload, employeeId }: { payload: CreateLeaveRequestPayload; employeeId?: string }) =>
      createLeaveRequest(payload, employeeId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: leaveKeys.all });
    },
  });
}

export function useApproveLeave() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({ leaveRequestId, remarks }: { leaveRequestId: string; remarks?: string }) =>
      approveLeave(leaveRequestId, { remarks }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: leaveKeys.all });
    },
  });
}

export function useRejectLeave() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({ leaveRequestId, remarks }: { leaveRequestId: string; remarks?: string }) =>
      rejectLeave(leaveRequestId, { remarks }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: leaveKeys.all });
    },
  });
}

export function useCancelLeave() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (leaveRequestId: string) => cancelLeave(leaveRequestId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: leaveKeys.all });
    },
  });
}

export function useInitializeLeaveBalances() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: InitializeLeaveBalancePayload) => initializeLeaveBalances(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: leaveKeys.all });
    },
  });
}

export function useCreateLeaveType() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: LeaveTypePayload) => createLeaveType(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: leaveKeys.leaveTypes() });
    },
  });
}

export function useUpdateLeaveType() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({ leaveTypeId, payload }: { leaveTypeId: string; payload: UpdateLeaveTypePayload }) =>
      updateLeaveType(leaveTypeId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: leaveKeys.leaveTypes() });
    },
  });
}

export function useDeleteLeaveType() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (leaveTypeId: string) => deleteLeaveType(leaveTypeId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: leaveKeys.leaveTypes() });
    },
  });
}
