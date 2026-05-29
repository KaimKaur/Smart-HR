"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useNotifications } from "@/hooks/use-notifications";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import type { RoleSlug } from "@/types/api";

const navConfig: Array<{ href: string; label: string; roles: RoleSlug[] }> = [
  { href: "/hr/dashboard", label: "HR Dashboard", roles: ["hr_manager", "system_administrator"] },
  {
    href: "/hr/dashboard/attendance",
    label: "Dashboard: Attendance",
    roles: ["hr_manager", "system_administrator"],
  },
  {
    href: "/hr/dashboard/performance",
    label: "Dashboard: Performance",
    roles: ["hr_manager", "system_administrator"],
  },
  { href: "/hr/employees", label: "Employees", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/reports/employees", label: "Employee Reports", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/reports/recruitment", label: "Recruitment Reports", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/reports/attendance", label: "Attendance Reports", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/reports/performance", label: "Performance Reports", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/performance/cycles", label: "Performance Cycles", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/performance/reviews/new", label: "New Review", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/attendance/daily", label: "Daily Attendance", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/attendance/corrections", label: "Corrections", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/attendance/monthly", label: "Monthly Attendance", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/leave", label: "Leave Requests", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/leave/approvals", label: "Leave Approvals", roles: ["hr_manager", "system_administrator"] },
  { href: "/hr/leave/balances", label: "Leave Balances", roles: ["hr_manager", "system_administrator"] },
  { href: "/employee/attendance", label: "My Attendance", roles: ["employee", "department_manager"] },
  { href: "/employee/leave", label: "My Leave", roles: ["employee", "department_manager"] },
  { href: "/employee/performance", label: "My Performance", roles: ["employee", "department_manager"] },
  { href: "/manager/performance/team", label: "Team Performance", roles: ["department_manager", "hr_manager", "system_administrator"] },
  { href: "/recruiter/jobs", label: "Jobs", roles: ["recruiter", "hr_manager", "system_administrator"] },
  { href: "/recruiter/interviews", label: "Interviews", roles: ["recruiter", "hr_manager", "system_administrator"] },
  {
    href: "/recruiter/dashboard",
    label: "Recruitment",
    roles: ["recruiter", "hr_manager", "system_administrator"],
  },
  { href: "/employee/dashboard", label: "My Dashboard", roles: ["employee", "department_manager"] },
  { href: "/admin/departments", label: "Departments", roles: ["hr_manager", "system_administrator"] },
  { href: "/admin/designations", label: "Designations", roles: ["hr_manager", "system_administrator"] },
  { href: "/admin/leave-types", label: "Leave Types", roles: ["hr_manager", "system_administrator"] },
  { href: "/admin/performance/metrics", label: "Performance Metrics", roles: ["hr_manager", "system_administrator"] },
  { href: "/notifications", label: "Notifications", roles: ["employee", "department_manager", "recruiter", "hr_manager", "system_administrator"] },
  { href: "/settings/notifications", label: "Notification Settings", roles: ["employee", "department_manager", "recruiter", "hr_manager", "system_administrator"] },
];

const adminSectionLinks: Array<{ href: string; label: string }> = [
  { href: "/admin/users", label: "Users" },
  { href: "/admin/roles", label: "Roles" },
  { href: "/admin/audit-logs", label: "Audit Logs" },
  { href: "/admin/settings", label: "Settings" },
  { href: "/admin/departments", label: "Departments" },
  { href: "/admin/designations", label: "Designations" },
  { href: "/admin/leave-types", label: "Leave Types" },
  { href: "/admin/performance/metrics", label: "Performance Metrics" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const roleSet = new Set<RoleSlug>(user?.roles ?? []);
  const unreadNotificationsQuery = useNotifications({ is_read: false, page: 1, page_size: 100 });

  const isSystemAdmin = roleSet.has("system_administrator");
  const links = navConfig.filter(
    (item) =>
      item.roles.some((role) => roleSet.has(role)) &&
      !adminSectionLinks.some((adminLink) => adminLink.href === item.href),
  );
  const leaveUnreadCount = (unreadNotificationsQuery.data?.items ?? []).filter((item) => {
    const haystack = `${item.title} ${item.message}`.toLowerCase();
    return haystack.includes("leave");
  }).length;

  return (
    <aside className="w-64 border-r bg-card p-4">
      <p className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        Smart HR
      </p>
      <nav className="space-y-1">
        {links.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center justify-between rounded-md px-3 py-2 text-sm",
              pathname === item.href ? "bg-primary text-primary-foreground" : "hover:bg-muted",
            )}
          >
            <span>{item.label}</span>
            {item.href === "/employee/leave" && leaveUnreadCount > 0 ? (
              <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">{leaveUnreadCount}</span>
            ) : null}
          </Link>
        ))}
        {isSystemAdmin ? (
          <div className="mt-4">
            <p className="mb-2 px-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Administration
            </p>
            <div className="space-y-1">
              {adminSectionLinks.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between rounded-md px-3 py-2 text-sm",
                    pathname === item.href ? "bg-primary text-primary-foreground" : "hover:bg-muted",
                  )}
                >
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          </div>
        ) : null}
      </nav>
    </aside>
  );
}
