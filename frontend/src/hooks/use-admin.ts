"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import {
  assignRole,
  createUser,
  deactivateUser,
  listUsers,
  updateUser,
  type CreateAdminUserPayload,
  type UpdateAdminUserPayload,
} from "@/services/admin-user.service";
import { listAuditLogs, type AuditLogFilters } from "@/services/audit-log.service";

export const adminKeys = {
  all: ["admin"] as const,
  users: (params?: { search?: string; page?: number; page_size?: number }) =>
    [...adminKeys.all, "users", params] as const,
  auditLogs: (params: AuditLogFilters) => [...adminKeys.all, "audit-logs", params] as const,
};

export function useUsers(params?: { search?: string; page?: number; page_size?: number }) {
  return useApiQuery({
    queryKey: adminKeys.users(params),
    queryFn: () => listUsers(params),
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: CreateAdminUserPayload) => createUser(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: adminKeys.all });
    },
  });
}

export function useUpdateUser(userId: string) {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: UpdateAdminUserPayload) => updateUser(userId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: adminKeys.all });
    },
  });
}

export function useDeactivateUser() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (userId: string) => deactivateUser(userId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: adminKeys.all });
    },
  });
}

export function useAssignRole(userId: string) {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (role: string) => assignRole(userId, role),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: adminKeys.all });
    },
  });
}

export function useAuditLogs(params: AuditLogFilters) {
  return useApiQuery({
    queryKey: adminKeys.auditLogs(params),
    queryFn: () => listAuditLogs(params),
  });
}

