"use client";

import { useApiQuery } from "@/hooks/use-api-query";
import {
  getAttendanceDashboard,
  getEmployeeDashboard,
  getHRDashboard,
  getPerformanceDashboard,
  getRecruitmentDashboard,
} from "@/services/dashboard.service";

const REFRESH_INTERVAL_MS = 60_000;

export const dashboardKeys = {
  all: ["dashboard"] as const,
  hr: () => [...dashboardKeys.all, "hr"] as const,
  recruitment: () => [...dashboardKeys.all, "recruitment"] as const,
  attendance: () => [...dashboardKeys.all, "attendance"] as const,
  performance: () => [...dashboardKeys.all, "performance"] as const,
  employee: () => [...dashboardKeys.all, "employee"] as const,
};

export function useHRDashboard() {
  return useApiQuery({
    queryKey: dashboardKeys.hr(),
    queryFn: getHRDashboard,
    refetchInterval: REFRESH_INTERVAL_MS,
  });
}

export function useRecruitmentDashboard() {
  return useApiQuery({
    queryKey: dashboardKeys.recruitment(),
    queryFn: getRecruitmentDashboard,
    refetchInterval: REFRESH_INTERVAL_MS,
  });
}

export function useAttendanceDashboard() {
  return useApiQuery({
    queryKey: dashboardKeys.attendance(),
    queryFn: getAttendanceDashboard,
    refetchInterval: REFRESH_INTERVAL_MS,
  });
}

export function usePerformanceDashboard() {
  return useApiQuery({
    queryKey: dashboardKeys.performance(),
    queryFn: getPerformanceDashboard,
    refetchInterval: REFRESH_INTERVAL_MS,
  });
}

export function useEmployeeDashboard() {
  return useApiQuery({
    queryKey: dashboardKeys.employee(),
    queryFn: getEmployeeDashboard,
    refetchInterval: REFRESH_INTERVAL_MS,
  });
}

