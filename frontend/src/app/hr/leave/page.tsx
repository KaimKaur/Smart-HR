"use client";

import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { useLeaveRequests, useLeaveTypes } from "@/hooks/use-leave";
import { useEmployees } from "@/hooks/use-employees";
import type { LeaveRequest } from "@/types/api";

export default function HrLeaveManagementPage() {
  const [filters, setFilters] = useState({
    employee_id: "",
    status: "",
    leave_type_id: "",
    date_from: "",
    date_to: "",
    page: 1,
  });

  const employeeQuery = useEmployees({ page: 1, page_size: 100 });
  const leaveTypesQuery = useLeaveTypes();

  const leaveQuery = useLeaveRequests({
    employee_id: filters.employee_id || undefined,
    status: filters.status || undefined,
    leave_type_id: filters.leave_type_id || undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    page: filters.page,
    page_size: 20,
  });

  const columns: DataTableColumn<LeaveRequest>[] = useMemo(
    () => [
      { key: "employee", header: "Employee", render: (row) => row.employee_name },
      { key: "type", header: "Leave type", render: (row) => row.leave_type_name },
      { key: "from", header: "Start", render: (row) => row.start_date },
      { key: "to", header: "End", render: (row) => row.end_date },
      {
        key: "status",
        header: "Status",
        render: (row) => <StatusBadge status={row.status} />,
      },
      {
        key: "reason",
        header: "Reason",
        render: (row) => row.reason ?? "—",
      },
    ],
    [],
  );

  const pagination = leaveQuery.data?.pagination;

  return (
    <div className="space-y-6">
      <PageHeader title="Leave management" description="Filter and review all leave requests." />
      <div className="grid gap-3 rounded-lg border bg-card p-4 sm:grid-cols-2 lg:grid-cols-5">
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Employee</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={filters.employee_id}
            onChange={(event) =>
              setFilters((current) => ({ ...current, employee_id: event.target.value, page: 1 }))
            }
          >
            <option value="">All</option>
            {(employeeQuery.data?.items ?? []).map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.full_name}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Status</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={filters.status}
            onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value, page: 1 }))}
          >
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Leave type</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={filters.leave_type_id}
            onChange={(event) =>
              setFilters((current) => ({ ...current, leave_type_id: event.target.value, page: 1 }))
            }
          >
            <option value="">All</option>
            {(leaveTypesQuery.data ?? []).map((type) => (
              <option key={type.id} value={type.id}>
                {type.name}
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
            onChange={(event) => setFilters((current) => ({ ...current, date_from: event.target.value, page: 1 }))}
          />
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">To</span>
          <input
            type="date"
            className="h-9 rounded-lg border px-3"
            value={filters.date_to}
            onChange={(event) => setFilters((current) => ({ ...current, date_to: event.target.value, page: 1 }))}
          />
        </label>
      </div>
      <DataTable
        columns={columns}
        rows={leaveQuery.data?.items ?? []}
        isLoading={leaveQuery.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No leave requests"
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
              onClick={() => setFilters((current) => ({ ...current, page: current.page - 1 }))}
            >
              Previous
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={pagination.page >= pagination.total_pages}
              onClick={() => setFilters((current) => ({ ...current, page: current.page + 1 }))}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
