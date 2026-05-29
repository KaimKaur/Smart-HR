"use client";

import Link from "next/link";
import { useMemo } from "react";

import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { Button } from "@/components/ui/button";
import { useEmployeeDashboard } from "@/hooks/use-dashboard";
import { useApiQuery } from "@/hooks/use-api-query";
import { useCheckIn, useCheckOut, useMyEmployeeId } from "@/hooks/use-attendance";
import { useToast } from "@/hooks/use-toast";
import { listNotifications } from "@/services/notification.service";

export default function EmployeeDashboardPage() {
  const toast = useToast();
  const dashboardQuery = useEmployeeDashboard();
  const employeeIdQuery = useMyEmployeeId();
  const employeeId = employeeIdQuery.data ?? undefined;
  const checkInMutation = useCheckIn();
  const checkOutMutation = useCheckOut();

  const notificationsQuery = useApiQuery({
    queryKey: ["notifications", "recent", "dashboard"],
    queryFn: () => listNotifications({ page: 1, page_size: 5 }),
    refetchInterval: 60_000,
  });

  const leaveWidget = useMemo(() => {
    const balances = dashboardQuery.data?.leave_balances ?? [];
    return balances.slice(0, 3);
  }, [dashboardQuery.data?.leave_balances]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="My dashboard"
        description="Quick actions and personal summaries. Auto-refreshes every 60 seconds."
        action={
          <div className="flex gap-2">
            <Button
              type="button"
              disabled={checkInMutation.isPending}
              onClick={async () => {
                await checkInMutation.mutateAsync(employeeId);
                toast.success("Checked in.");
              }}
            >
              Check in
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={checkOutMutation.isPending}
              onClick={async () => {
                await checkOutMutation.mutateAsync(employeeId);
                toast.success("Checked out.");
              }}
            >
              Check out
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Attendance (this month)"
          value={
            dashboardQuery.data?.attendance_this_month
              ? `${dashboardQuery.data.attendance_this_month.present_days} days`
              : "—"
          }
          subtitle={
            dashboardQuery.data?.attendance_this_month
              ? `${dashboardQuery.data.attendance_this_month.total_hours.toFixed(1)} hours`
              : undefined
          }
          isLoading={dashboardQuery.isLoading}
        />
        <StatCard
          title="Latest performance"
          value={
            dashboardQuery.data?.latest_performance_rating != null
              ? dashboardQuery.data.latest_performance_rating.toFixed(1)
              : "—"
          }
          subtitle="Rating out of 5"
          isLoading={dashboardQuery.isLoading}
        />
        <StatCard
          title="Unread notifications"
          value={dashboardQuery.data?.unread_notifications_count}
          isLoading={dashboardQuery.isLoading}
        />
        <StatCard
          title="Leave balance types"
          value={dashboardQuery.data?.leave_balances.length ?? 0}
          isLoading={dashboardQuery.isLoading}
        />
      </div>

      <section className="rounded-xl border bg-card p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Leave balances</h2>
          <Link className="text-sm text-primary hover:underline" href="/employee/leave">
            Apply for leave
          </Link>
        </div>
        {!leaveWidget.length ? (
          <p className="mt-3 text-sm text-muted-foreground">No leave balances available.</p>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {leaveWidget.map((item) => (
              <div key={item.leave_type_id} className="rounded-lg border p-3">
                <p className="text-sm font-medium">{item.leave_type_name}</p>
                <p className="mt-1 text-sm text-muted-foreground">{item.balance.toFixed(1)} remaining</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-xl border bg-card p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Recent notifications</h2>
          <Link className="text-sm text-primary hover:underline" href="/notifications">
            View all
          </Link>
        </div>
        <ul className="mt-3 space-y-2">
          {(notificationsQuery.data?.items ?? []).map((n) => (
            <li key={n.id} className="rounded-lg border p-3">
              <p className="text-sm font-medium">{n.title}</p>
              <p className="text-sm text-muted-foreground">{n.message}</p>
              <p className="mt-2 text-xs text-muted-foreground">{new Date(n.created_at).toLocaleString()}</p>
            </li>
          ))}
          {!notificationsQuery.isLoading && !(notificationsQuery.data?.items ?? []).length ? (
            <p className="text-sm text-muted-foreground">No recent notifications.</p>
          ) : null}
        </ul>
      </section>
    </div>
  );
}

