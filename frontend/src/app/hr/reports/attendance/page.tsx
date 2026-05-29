"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { useApiQuery } from "@/hooks/use-api-query";
import { useToast } from "@/hooks/use-toast";
import { downloadBlob } from "@/lib/download";
import { listDepartments, listAttendanceStatuses } from "@/services/organization.service";
import { exportAttendanceReport, getAttendanceReport } from "@/services/reporting.service";
import { listEmployees } from "@/services/employee.service";
import type { AttendanceReportRow } from "@/types/api";

function daysAgoIso(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().slice(0, 10);
}

export default function AttendanceReportPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [isExporting, setIsExporting] = useState(false);

  const filters = useMemo(
    () => ({
      employee_id: searchParams.get("employee_id") || undefined,
      department_id: searchParams.get("department_id") || undefined,
      date_from: searchParams.get("date_from") || daysAgoIso(30),
      date_to: searchParams.get("date_to") || new Date().toISOString().slice(0, 10),
      status: searchParams.get("status") || undefined,
      page: Number(searchParams.get("page") || "1"),
      page_size: 20,
    }),
    [searchParams],
  );

  const reportQuery = useApiQuery({
    queryKey: ["attendance-report", filters],
    queryFn: () => getAttendanceReport(filters),
  });

  const departmentsQuery = useApiQuery({
    queryKey: ["departments", "all"],
    queryFn: () => listDepartments(1, 100),
  });

  const statusesQuery = useApiQuery({
    queryKey: ["attendance-statuses"],
    queryFn: listAttendanceStatuses,
  });

  const employeesQuery = useApiQuery({
    queryKey: ["employees", "report-filter"],
    queryFn: () => listEmployees({ page: 1, page_size: 100 }),
  });

  const updateParams = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      Object.entries(updates).forEach(([key, value]) => {
        if (!value) params.delete(key);
        else params.set(key, value);
      });
      router.replace(`/hr/reports/attendance?${params.toString()}`);
    },
    [router, searchParams],
  );

  const columns: DataTableColumn<AttendanceReportRow>[] = [
    { key: "name", header: "Employee", render: (row) => row.full_name },
    { key: "code", header: "Code", render: (row) => row.employee_code },
    { key: "department", header: "Department", render: (row) => row.department_name },
    { key: "date", header: "Date", render: (row) => row.attendance_date },
    { key: "status", header: "Status", render: (row) => row.status_name },
    { key: "in", header: "Check in", render: (row) => row.check_in_time ?? "—" },
    { key: "out", header: "Check out", render: (row) => row.check_out_time ?? "—" },
  ];

  const pagination = reportQuery.data?.pagination;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance report"
        description="Filter attendance records and export to CSV."
        action={
          <Button
            type="button"
            disabled={isExporting}
            onClick={async () => {
              setIsExporting(true);
              try {
                const blob = await exportAttendanceReport({
                  employee_id: filters.employee_id,
                  department_id: filters.department_id,
                  date_from: filters.date_from,
                  date_to: filters.date_to,
                  status: filters.status,
                });
                downloadBlob(blob, "attendance_report.csv");
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

      <div className="grid gap-3 rounded-lg border bg-card p-4 sm:grid-cols-2 lg:grid-cols-5">
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Employee</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={filters.employee_id ?? ""}
            onChange={(event) => updateParams({ employee_id: event.target.value || null, page: "1" })}
          >
            <option value="">All</option>
            {(employeesQuery.data?.items ?? []).map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.full_name}
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
          <span className="font-medium">Status</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={filters.status ?? ""}
            onChange={(event) => updateParams({ status: event.target.value || null, page: "1" })}
          >
            <option value="">All</option>
            {(statusesQuery.data ?? []).map((status) => (
              <option key={status.id} value={status.name}>
                {status.name}
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

      <DataTable
        columns={columns}
        rows={reportQuery.data?.items ?? []}
        isLoading={reportQuery.isLoading}
        getRowKey={(row) => row.record_id}
        emptyTitle="No attendance records"
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
    </div>
  );
}
