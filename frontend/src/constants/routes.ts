import type { RoleSlug } from "@/types/api";

export const PUBLIC_ROUTES = ["/login", "/forgot-password", "/reset-password"] as const;

export const DEFAULT_DASHBOARD_BY_ROLE: Record<RoleSlug, string> = {
  system_administrator: "/admin/dashboard",
  hr_manager: "/hr/dashboard",
  recruiter: "/recruiter/dashboard",
  department_manager: "/manager/dashboard",
  employee: "/employee/dashboard",
};

export const PROTECTED_ROUTE_RULES: Array<{ prefix: string; roles: RoleSlug[] }> = [
  {
    prefix: "/admin",
    roles: ["system_administrator", "hr_manager"],
  },
  {
    prefix: "/hr",
    roles: ["system_administrator", "hr_manager"],
  },
  {
    prefix: "/recruiter",
    roles: ["system_administrator", "hr_manager", "recruiter"],
  },
  {
    prefix: "/manager",
    roles: ["system_administrator", "department_manager", "hr_manager"],
  },
  {
    prefix: "/employee",
    roles: ["employee", "department_manager", "hr_manager", "system_administrator"],
  },
];
