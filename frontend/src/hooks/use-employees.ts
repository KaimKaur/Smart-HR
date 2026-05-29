"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import {
  createEmployee,
  deactivateEmployee,
  getEmployee,
  listEmployees,
  type CreateEmployeePayload,
  type EmployeeListFilters,
  type UpdateEmployeePayload,
  updateEmployee,
} from "@/services/employee.service";

export const employeeKeys = {
  all: ["employees"] as const,
  lists: () => [...employeeKeys.all, "list"] as const,
  list: (filters: EmployeeListFilters) => [...employeeKeys.lists(), filters] as const,
  details: () => [...employeeKeys.all, "detail"] as const,
  detail: (id: string) => [...employeeKeys.details(), id] as const,
};

export function useEmployees(filters: EmployeeListFilters = {}) {
  return useApiQuery({
    queryKey: employeeKeys.list(filters),
    queryFn: () => listEmployees(filters),
  });
}

export function useEmployee(id: string | undefined) {
  return useApiQuery({
    queryKey: employeeKeys.detail(id ?? ""),
    queryFn: () => getEmployee(id!),
    enabled: Boolean(id),
  });
}

export function useCreateEmployee() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: CreateEmployeePayload) => createEmployee(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: employeeKeys.lists() });
    },
  });
}

export function useUpdateEmployee(id: string) {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: UpdateEmployeePayload) => updateEmployee(id, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: employeeKeys.lists() });
      await queryClient.invalidateQueries({ queryKey: employeeKeys.detail(id) });
    },
  });
}

export function useDeactivateEmployee() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (id: string) => deactivateEmployee(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: employeeKeys.lists() });
    },
  });
}
