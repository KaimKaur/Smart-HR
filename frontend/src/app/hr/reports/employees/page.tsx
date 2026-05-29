"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { useApiQuery } from "@/hooks/use-api-query";
import { useToast } from "@/hooks/use-toast";
import { downloadBlob } from "@/lib/download";
import {
  listDepartments,
  listDesignations,
  listEmploymentStatuses,
} from "@/services/organization.service";
import { exportEmployeeReport, getEmployeeReport } from "@/services/reporting.service";
import type { EmployeeReportRow } from "@/types/api";

export default function EmployeeReportPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [isExporting, setIsExporting] = useState(false);

  const filters = useMemo(
    () => ({
      department_id: searchParams.get("department_id") || undefined,
      designation_id: searchParams.get("designation_id") || undefined,
      employment_status_id: searchParams.get("employment_status_id") || undefined,
      date_from: searchParams.get("date_from") || undefined,
      page: Number(searchParams.get("page") || "1"),
      page_size: Number(searchParams.get("page_size") || "20"),
    }),
    [searchParams],
  );

  const reportQuery = useApiQuery({
    queryKey: ["employee-report", filters],
    queryFn: () => getEmployeeReport(filters),
  });

  const departmentsQuery = useApiQuery({
    queryKey: ["departments", "all"],
    queryFn: () => listDepartments(1, 100),
  });
  const designationsQuery = useApiQuery({
    queryKey: ["designations", "all"],
    queryFn: () => listDesignations(1, 100),
  });
  const statusesQuery = useApiQuery({
    queryKey: ["employment-statuses"],
    queryFn: listEmploymentStatuses,
  });

  const updateParams = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      Object.entries(updates).forEach(([key, value]) => {
        if (!value) params.delete(key);
        else params.set(key, value);
      });
      router.replace(`/hr/reports/employees?${params.toString()}`);
    },
    [router, searchParams],
  );

  const columns: DataTableColumn<EmployeeReportRow>[] = [
    { key: "name", header: "Name", render: (row) => row.full_name },
    { key: "code", header: "Code", render: (row) => row.employee_code },
    { key: "email", header: "Email", render: (row) => row.email },
    { key: "department", header: "Department", render: (row) => row.department_name },
    { key: "designation", header: "Designation", render: (row) => row.designation_title },
    { key: "status", header: "Status", render: (row) => row.employment_status },
    { key: "join_date", header: "Join date", render: (row) => row.join_date },
  ];

  const pagination = reportQuery.data?.pagination;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Employee report"
        description="Filter employee records and export to CSV."
        action={
          <Button
            type="button"
            disabled={isExporting}
            onClick={async () => {
              setIsExporting(true);
              try {
                const blob = await exportEmployeeReport({
                  department_id: filters.department_id,
                  designation_id: filters.designation_id,
                  employment_status_id: filters.employment_status_id,
                  date_from: filters.date_from,
                });
                downloadBlob(blob, "employees_report.csv");
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
          <span className="font-medium">Department</span>
          <select
            className="h-9 rounded-lg border bg-background px-3"
            value={filters.department_id ?? ""}
            onChange={(event) =>
              updateParams({ department_id: event.target.value || null, page: "1" })
            }
          >
            <option value="">All</option>
            {(departmentsQuery.data?.items ?? []).map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Designation</span>
          <select
            className="h-9 rounded-lg border bg-background px-3"
            value={filters.designation_id ?? ""}
            onChange={(event) =>
              updateParams({ designation_id: event.target.value || null, page: "1" })
            }
          >
            <option value="">All</option>
            {(designationsQuery.data?.items ?? []).map((d) => (
              <option key={d.id} value={d.id}>
                {d.title}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Employment status</span>
          <select
            className="h-9 rounded-lg border bg-background px-3"
            value={filters.employment_status_id ?? ""}
            onChange={(event) =>
              updateParams({ employment_status_id: event.target.value || null, page: "1" })
            }
          >
            <option value="">All</option>
            {(statusesQuery.data ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Joined from</span>
          <input
            type="date"
            className="h-9 rounded-lg border bg-background px-3"
            value={filters.date_from ?? ""}
            onChange={(event) =>
              updateParams({ date_from: event.target.value || null, page: "1" })
            }
          />
        </label>
      </div>

      <DataTable
        columns={columns}
        rows={reportQuery.data?.items ?? []}
        isLoading={reportQuery.isLoading}
        getRowKey={(row) => row.employee_id}
        emptyTitle="No report rows"
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
