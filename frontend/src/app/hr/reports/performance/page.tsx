'use client'

"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
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
import { Button } from "@/components/ui/button";
import { useApiQuery } from "@/hooks/use-api-query";
import { useCycles } from "@/hooks/use-performance";
import { useToast } from "@/hooks/use-toast";
import { downloadBlob } from "@/lib/download";
import { listDepartments } from "@/services/organization.service";
import { exportPerformanceReport, getPerformanceReport } from "@/services/performance.service";
import type { PerformanceReportEmployeeRow, TopPerformer } from "@/types/api";

function daysAgoIso(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().slice(0, 10);
}

export default function PerformanceReportPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [isExporting, setIsExporting] = useState(false);

  const filters = useMemo(
    () => ({
      cycle_id: searchParams.get("cycle_id") || undefined,
      department_id: searchParams.get("department_id") || undefined,
      date_from: searchParams.get("date_from") || daysAgoIso(365),
      date_to: searchParams.get("date_to") || new Date().toISOString().slice(0, 10),
      page: Number(searchParams.get("page") || "1"),
      page_size: 20,
    }),
    [searchParams],
  );

  const reportQuery = useApiQuery({
    queryKey: ["performance-report", filters],
    queryFn: () => getPerformanceReport(filters),
  });

  const cyclesQuery = useCycles(1, 100);
  const departmentsQuery = useApiQuery({
    queryKey: ["departments", "performance-report"],
    queryFn: () => listDepartments(1, 100),
  });

  const updateParams = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      Object.entries(updates).forEach(([key, value]) => {
        if (!value) params.delete(key);
        else params.set(key, value);
      });
      router.replace(`/hr/reports/performance?${params.toString()}`);
    },
    [router, searchParams],
  );

  const departmentChartData =
    reportQuery.data?.average_rating_per_department.map((row) => ({
      department: row.department_name,
      rating: row.average_rating ?? 0,
    })) ?? [];

  const topPerformers = (reportQuery.data?.top_performers ?? []).filter(
    (row) => (row.average_rating ?? 0) >= 4,
  );

  const topPerformerColumns: DataTableColumn<TopPerformer>[] = [
    { key: "name", header: "Employee", render: (row) => row.employee.full_name },
    { key: "code", header: "Code", render: (row) => row.employee.employee_code },
    {
      key: "department",
      header: "Department",
      render: (row) => row.employee.department_name ?? "—",
    },
    {
      key: "rating",
      header: "Average rating",
      render: (row) => (row.average_rating != null ? row.average_rating.toFixed(1) : "—"),
    },
  ];

  const employeeColumns: DataTableColumn<PerformanceReportEmployeeRow>[] = [
    { key: "name", header: "Employee", render: (row) => row.employee.full_name },
    { key: "code", header: "Code", render: (row) => row.employee.employee_code },
    {
      key: "rating",
      header: "Avg rating",
      render: (row) => (row.average_rating != null ? row.average_rating.toFixed(1) : "—"),
    },
    {
      key: "score",
      header: "Avg score",
      render: (row) => (row.average_score != null ? row.average_score.toFixed(1) : "—"),
    },
  ];

  const pagination = reportQuery.data?.pagination;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Performance report"
        description="Department averages, top performers, and score distribution."
        action={
          <Button
            type="button"
            disabled={isExporting}
            onClick={async () => {
              setIsExporting(true);
              try {
                const blob = await exportPerformanceReport({
                  cycle_id: filters.cycle_id,
                  department_id: filters.department_id,
                  date_from: filters.date_from,
                  date_to: filters.date_to,
                });
                downloadBlob(blob, "performance_report.csv");
                toast.success("CSV export downloaded.");
              } catch {
                toast.error("Unable to export report.");
              } finally {
                setIsExporting(false);
              }
            }}
          >
            {isExporting ? "Exporting..." : "Export CSV"}
          </Button>
        }
      />

      <div className="grid gap-3 rounded-lg border bg-card p-4 sm:grid-cols-2 lg:grid-cols-4">
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Cycle</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={filters.cycle_id ?? ""}
            onChange={(event) => updateParams({ cycle_id: event.target.value || null, page: "1" })}
          >
            <option value="">All</option>
            {(cyclesQuery.data?.items ?? []).map((cycle) => (
              <option key={cycle.id} value={cycle.id}>
                {cycle.name}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Department</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={filters.department_id ?? ""}
            onChange={(event) => updateParams({ department_id: event.target.value || null, page: "1" })}
          >
            <option value="">All</option>
            {(departmentsQuery.data?.items ?? []).map((department) => (
              <option key={department.id} value={department.id}>
                {department.name}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">From</span>
          <input
            type="date"
            className="h-9 rounded-lg border px-3"
            value={filters.date_from}
            onChange={(event) => updateParams({ date_from: event.target.value, page: "1" })}
          />
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">To</span>
          <input
            type="date"
            className="h-9 rounded-lg border px-3"
            value={filters.date_to}
            onChange={(event) => updateParams({ date_to: event.target.value, page: "1" })}
          />
        </label>
      </div>

      <section className="rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-base font-semibold">Average rating per department</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={departmentChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="department" />
              <YAxis domain={[0, 5]} />
              <Tooltip />
              <Bar dataKey="rating" fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Top performers (rating ≥ 4)</h2>
        <DataTable
          columns={topPerformerColumns}
          rows={topPerformers}
          isLoading={reportQuery.isLoading}
          getRowKey={(row) => row.employee.id}
          emptyTitle="No top performers"
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Score distribution</h2>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {(reportQuery.data?.score_distribution ?? []).map((bucket) => (
            <div key={bucket.bucket} className="rounded-lg border p-3 text-sm">
              <p className="font-medium">{bucket.bucket}</p>
              <p className="text-muted-foreground">
                {bucket.count} ({bucket.percentage.toFixed(1)}%)
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Employees</h2>
        <DataTable
          columns={employeeColumns}
          rows={reportQuery.data?.employees ?? []}
          isLoading={reportQuery.isLoading}
          getRowKey={(row) => row.employee.id}
          emptyTitle="No employee performance data"
        />
        {pagination ? (
          <div className="flex items-center justify-between text-sm">
            <p className="text-muted-foreground">
              Page {pagination.page} of {pagination.total_pages} ({pagination.total_items} total)
            </p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                disabled={pagination.page <= 1}
                onClick={() => updateParams({ page: String(pagination.page - 1) })}
              >
                Previous
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={pagination.page >= pagination.total_pages}
                onClick={() => updateParams({ page: String(pagination.page + 1) })}
              >
                Next
              </Button>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}
