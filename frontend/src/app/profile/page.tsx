"use client";

import Link from "next/link";

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

export default function ProfilePage() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading...</div>;
  }

  if (!user) {
    return (
      <div className="p-4">
        <p className="text-sm text-muted-foreground">You are not signed in.</p>
        <div className="mt-4">
          <Button asChild>
            <Link href="/login">Go to login</Link>
          </Button>
        </div>
      </div>
    );
  }

  const dashboardHref = getDashboardForRoles(user.roles);

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold tracking-tight">Profile</h1>
      <p className="mt-2 text-sm text-muted-foreground">Your account details.</p>

      <div className="mt-6 space-y-2 rounded-xl border bg-card p-4">
        <div className="text-sm">
          <span className="font-medium">Email:</span> {user.email}
        </div>
        <div className="text-sm">
          <span className="font-medium">Roles:</span> {user.roles.join(", ")}
        </div>
      </div>

      <div className="mt-6 flex gap-2">
        <Button asChild>
          <Link href={dashboardHref}>Back to dashboard</Link>
        </Button>
      </div>
    </div>
  );
}

