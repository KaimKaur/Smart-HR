"use client";

import Link from "next/link";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { DEFAULT_DASHBOARD_BY_ROLE } from "@/constants/routes";
import { useAuth } from "@/hooks/useAuth";
import type { RoleSlug } from "@/types/api";

const ROLE_PRIORITY: RoleSlug[] = [
  "system_administrator",
  "hr_manager",
  "recruiter",
  "department_manager",
  "employee",
];

function getDashboardForRoles(roles: RoleSlug[]): string {
  const matched = ROLE_PRIORITY.find((role) => roles.includes(role));
  if (!matched) return "/employee/dashboard";
  return DEFAULT_DASHBOARD_BY_ROLE[matched];
}

export default function UnauthorizedPage() {
  const { user } = useAuth();

  const dashboardHref = useMemo(() => {
    if (!user) return "/login";
    return getDashboardForRoles(user.roles);
  }, [user]);

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-lg rounded-xl border bg-card p-6 shadow-sm">
        <h1 className="text-2xl font-semibold tracking-tight">Access denied</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          You don&apos;t have permission to view this page.
        </p>
        <div className="mt-6 flex flex-wrap gap-2">
          <Button asChild>
            <Link href={dashboardHref}>Go to dashboard</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/login">Sign in as different user</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

