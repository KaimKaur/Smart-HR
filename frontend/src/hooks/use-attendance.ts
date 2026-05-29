"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import { useAuth } from "@/hooks/useAuth";
import { listEmployees } from "@/services/employee.service";
import {
  checkIn,
  checkOut,
  getDailyAttendance,
  getMonthlySummary,
  listAttendance,
  listCorrections,
  listPendingCorrections,
  requestCorrection,
  reviewCorrection,
  type AttendanceListFilters,
} from "@/services/attendance.service";

export const attendanceKeys = {
  all: ["attendance"] as const,
  list: (filters: AttendanceListFilters) => [...attendanceKeys.all, "list", filters] as const,
  monthly: (employeeId: string, year: number, month: number) =>
    [...attendanceKeys.all, "monthly", employeeId, year, month] as const,
  daily: (date: string) => [...attendanceKeys.all, "daily", date] as const,
  corrections: (recordId: string) => [...attendanceKeys.all, "corrections", recordId] as const,
  pendingCorrections: (dateFrom: string, dateTo: string) =>
    [...attendanceKeys.all, "pending-corrections", dateFrom, dateTo] as const,
};

export function useMyEmployeeId() {
  const { user } = useAuth();
  return useApiQuery({
    queryKey: ["my-employee-id", user?.email],
    queryFn: async () => {
      if (!user?.email) return null;
      const result = await listEmployees({ search: user.email, page: 1, page_size: 1 });
      return result.items[0]?.id ?? null;
    },
    enabled: Boolean(user?.email),
  });
}

export function useAttendanceHistory(filters: AttendanceListFilters = {}) {
  return useApiQuery({
    queryKey: attendanceKeys.list(filters),
    queryFn: () => listAttendance(filters),
  });
}

export function useMonthlySummary(
  employeeId: string | undefined,
  year: number,
  month: number,
) {
  return useApiQuery({
    queryKey: attendanceKeys.monthly(employeeId ?? "", year, month),
    queryFn: () => getMonthlySummary(employeeId!, year, month),
    enabled: Boolean(employeeId),
  });
}

export function useDailyAttendance(date: string) {
  return useApiQuery({
    queryKey: attendanceKeys.daily(date),
    queryFn: () => getDailyAttendance(date),
    enabled: Boolean(date),
  });
}

export function useRecordCorrections(recordId: string | undefined) {
  return useApiQuery({
    queryKey: attendanceKeys.corrections(recordId ?? ""),
    queryFn: () => listCorrections(recordId!),
    enabled: Boolean(recordId),
  });
}

export function usePendingCorrections(dateFrom: string, dateTo: string) {
  return useApiQuery({
    queryKey: attendanceKeys.pendingCorrections(dateFrom, dateTo),
    queryFn: () => listPendingCorrections(dateFrom, dateTo),
    enabled: Boolean(dateFrom && dateTo),
  });
}

export function useCheckIn() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (employeeId?: string) => checkIn(employeeId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: attendanceKeys.all });
    },
  });
}

export function useCheckOut() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (employeeId?: string) => checkOut(employeeId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: attendanceKeys.all });
    },
  });
}

export function useCreateCorrection() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({ recordId, reason }: { recordId: string; reason: string }) =>
      requestCorrection(recordId, reason),
    onSuccess: async (_data, { recordId }) => {
      await queryClient.invalidateQueries({ queryKey: attendanceKeys.corrections(recordId) });
      await queryClient.invalidateQueries({ queryKey: attendanceKeys.all });
    },
  });
}

export function useReviewCorrection() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: ({
      correctionId,
      status,
    }: {
      correctionId: string;
      status: "approved" | "rejected";
    }) => reviewCorrection(correctionId, status),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: attendanceKeys.all });
    },
  });
}
