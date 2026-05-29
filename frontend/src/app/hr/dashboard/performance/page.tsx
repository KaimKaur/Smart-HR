'use client'

"use client";

import Link from "next/link";
import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { usePerformanceDashboard } from "@/hooks/use-dashboard";
import { useApiQuery } from "@/hooks/use-api-query";
import { getPerformanceReport } from "@/services/performance.service";
import type { TopPerformer } from "@/types/api";

function daysAgoIso(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().slice(0, 10);
}

export default function PerformanceDashboardPage() {
  const dashboardQuery = usePerformanceDashboard();
  const data = dashboardQuery.data;

  const reportQuery = useApiQuery({
    queryKey: ["performance-report", "dashboard", data?.active_cycle_id],
    queryFn: () =>
      getPerformanceReport({
        cycle_id: data?.active_cycle_id ?? undefined,
        date_from: daysAgoIso(365),
        date_to: new Date().toISOString().slice(0, 10),
        page: 1,
        page_size: 20,
      }),
    enabled: Boolean(data?.active_cycle_id),
    refetchInterval: 60_000,
  });

  const deptChartData =
    reportQuery.data?.average_rating_per_department.map((row) => ({
      department: row.department_name,
      rating: row.average_rating ?? 0,
    })) ?? [];

  const topPerformersFromReport: TopPerformer[] = (reportQuery.data?.top_performers ?? []).filter(
    (row) => (row.average_rating ?? 0) >= 4,
  );

  const topPerformersFallback = useMemo(() => {
    return (data?.top_performers ?? []).map((row) => ({
      employee: {
        id: row.employee_id,
        employee_code: row.employee_code,
        full_name: row.full_name,
        department_name: row.department_name ?? null,
      },
      average_rating: row.rating,
    }));
  }, [data?.top_performers]);

  const topPerformerRows = topPerformersFromReport.length ? topPerformersFromReport : topPerformersFallback;

  const topPerformerColumns: DataTableColumn<TopPerformer>[] = [
    {
      key: "employee",
      header: "Employee",
      render: (row) => (
        <Link className="text-primary hover:underline" href={`/hr/employees/${row.employee.id}`}>
          {row.employee.full_name}
        </Link>
      ),
    },
    { key: "code", header: "Code", render: (row) => row.employee.employee_code },
    { key: "department", header: "Department", render: (row) => row.employee.department_name ?? "—" },
    {
      key: "rating",
      header: "Rating",
      render: (row) => (row.average_rating != null ? row.average_rating.toFixed(1) : "—"),
    },
  ];

  const activeCycleName = data?.active_cycle_name;

  if (!activeCycleName) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Performance dashboard"
          description="No active performance cycle is configured."
        />
        <div className="rounded-xl border bg-card p-6">
          <p className="text-sm text-muted-foreground">
            Create or activate a cycle to see performance KPIs and department averages.
          </p>
          <Link className="mt-3 inline-block text-sm text-primary hover:underline" href="/hr/performance/cycles">
            Go to performance cycles
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Performance dashboard"
        description={`Active cycle: ${activeCycleName}`}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Average rating"
          value={data?.average_rating != null ? data.average_rating.toFixed(2) : "—"}
          isLoading={dashboardQuery.isLoading}
        />
        <StatCard
          title="Top performers"
          value={topPerformerRows.length}
          subtitle="Rating ≥ 4"
          isLoading={dashboardQuery.isLoading}
        />
        <StatCard
          title="Pending reviews"
          value={data?.employees_without_review ?? 0}
          subtitle="Employees without a review"
          isLoading={dashboardQuery.isLoading}
        />
      </div>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-4 text-base font-semibold">Average rating by department</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={deptChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department" hide />
                <YAxis domain={[0, 5]} />
                <Tooltip />
                <Bar dataKey="rating" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Chart sourced from `GET /reports/performance` (cycle-filtered when active cycle exists).
          </p>
        </div>

        <div className="space-y-3 rounded-xl border bg-card p-4">
          <h2 className="text-base font-semibold">Top performers</h2>
          <DataTable
            columns={topPerformerColumns}
            rows={topPerformerRows}
            isLoading={dashboardQuery.isLoading || reportQuery.isLoading}
            getRowKey={(row) => row.employee.id}
            emptyTitle="No top performers"
          />
        </div>
      </section>
    </div>
  );
}

