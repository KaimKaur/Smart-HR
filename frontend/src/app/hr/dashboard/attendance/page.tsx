'use client'

"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { useAttendanceDashboard } from "@/hooks/use-dashboard";

export default function AttendanceDashboardPage() {
  const dashboardQuery = useAttendanceDashboard();
  const data = dashboardQuery.data;

  const trend =
    data?.weekly_trend?.map((point) => ({
      date: point.date,
      present: point.present_count,
      absent: point.absent_count,
    })) ?? [];

  const topAbsent = (data?.top_absent_departments ?? []).slice().sort((a, b) => b.absent_count - a.absent_count);
  const highestAbsence = topAbsent[0];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance dashboard"
        description="Today's attendance and 7-day trend. Auto-refreshes every 60 seconds."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Present (today)" value={data?.present_count} isLoading={dashboardQuery.isLoading} />
        <StatCard title="Absent (today)" value={data?.absent_count} isLoading={dashboardQuery.isLoading} />
        <StatCard title="Late (today)" value={data?.late_count} isLoading={dashboardQuery.isLoading} />
        <StatCard
          title="Attendance rate (today)"
          value={data ? `${data.attendance_rate_today.toFixed(1)}%` : undefined}
          isLoading={dashboardQuery.isLoading}
        />
      </div>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-4 text-base font-semibold">Weekly attendance trend</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="present" stroke="#16a34a" fill="#16a34a" fillOpacity={0.15} />
                <Area type="monotone" dataKey="absent" stroke="#dc2626" fill="#dc2626" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-4 text-base font-semibold">Department breakdown</h2>
          {highestAbsence ? (
            <div className="mb-4 rounded-lg border bg-muted/20 p-3 text-sm">
              <p className="font-medium">Highest absence</p>
              <p className="text-muted-foreground">
                {highestAbsence.department_name} — {highestAbsence.absent_count} absent
              </p>
            </div>
          ) : null}

          <div className="space-y-2">
            {topAbsent.length ? (
              topAbsent.map((dept) => (
                <div key={dept.department_id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                  <span>{dept.department_name}</span>
                  <span className="text-muted-foreground">{dept.absent_count} absent</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No department absence data available.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

