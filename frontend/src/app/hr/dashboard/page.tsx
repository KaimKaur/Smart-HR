"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { useAttendanceDashboard, useHRDashboard } from "@/hooks/use-dashboard";
import { useApiQuery } from "@/hooks/use-api-query";
import { listDepartments } from "@/services/organization.service";

function percent(value: number) {
  return `${value.toFixed(1)}%`;
}

export default function HrDashboardPage() {
  const hrQuery = useHRDashboard();
  const attendanceQuery = useAttendanceDashboard();
  const departmentsQuery = useApiQuery({
    queryKey: ["departments", "dashboard"],
    queryFn: () => listDepartments(1, 100),
    refetchInterval: 60_000,
  });

  const hr = hrQuery.data;
  const weeklyTrend =
    attendanceQuery.data?.weekly_trend?.map((point) => ({
      date: point.date,
      present: point.present_count,
      absent: point.absent_count,
    })) ?? [];

  const headcount =
    (departmentsQuery.data?.items ?? []).map((dept) => ({
      department: dept.name,
      count: dept.employee_count,
    })) ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="HR dashboard"
        description="Key HR KPIs and trends. Auto-refreshes every 60 seconds."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard title="Total employees" value={hr?.total_employees} isLoading={hrQuery.isLoading} />
        <StatCard title="Active employees" value={hr?.active_employees} isLoading={hrQuery.isLoading} />
        <StatCard
          title="New hires (30d)"
          value={hr?.new_hires_last_30_days}
          isLoading={hrQuery.isLoading}
        />
        <StatCard title="Open jobs" value={hr?.open_job_postings} isLoading={hrQuery.isLoading} />
        <StatCard
          title="Pending leaves"
          value={hr?.pending_leave_requests_count}
          isLoading={hrQuery.isLoading}
        />
        <StatCard
          title="Attendance rate (today)"
          value={hr ? percent(hr.attendance_rate_today) : undefined}
          isLoading={hrQuery.isLoading}
        />
      </div>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-4 text-base font-semibold">Attendance trend (7 days)</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weeklyTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="present" stroke="#16a34a" strokeWidth={2} />
                <Line type="monotone" dataKey="absent" stroke="#dc2626" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Note: backend `GET /dashboard/hr` does not include trend points, so this chart is sourced from
            `GET /dashboard/attendance`.
          </p>
        </div>

        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-4 text-base font-semibold">Department headcount</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={headcount}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Note: headcount is derived from `GET /departments` employee counts.
          </p>
        </div>
      </section>
    </div>
  );
}

