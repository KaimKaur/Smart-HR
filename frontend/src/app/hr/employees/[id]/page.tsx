"use client";

import axios from "axios";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { PageHeader } from "@/components/common/page-header";
import { EmployeeForm } from "@/components/employees/employee-form";
import { Button } from "@/components/ui/button";
import { useApiQuery } from "@/hooks/use-api-query";
import { useDeactivateEmployee, useEmployee, useUpdateEmployee } from "@/hooks/use-employees";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/services/api";
import type {
  AttendanceRecord,
  ErrorResponse,
  LeaveRequest,
  PaginatedResponse,
  SuccessResponse,
} from "@/types/api";

type Tab = "profile" | "attendance" | "leave" | "performance";

type LeaveHistoryItem = LeaveRequest;

interface PerformanceHistoryItem {
  review_id: string;
  cycle: { id: string; name: string };
  rating: number;
}

export default function EmployeeDetailPage() {
  const params = useParams<{ id: string }>();
  const employeeId = params.id;
  const toast = useToast();
  const { hasRole } = useAuth();
  const canEdit = hasRole("hr_manager") || hasRole("system_administrator");
  const canDeactivate = hasRole("system_administrator");

  const [tab, setTab] = useState<Tab>("profile");
  const [showEdit, setShowEdit] = useState(false);
  const [showDeactivate, setShowDeactivate] = useState(false);

  const employeeQuery = useEmployee(employeeId);
  const updateMutation = useUpdateEmployee(employeeId);
  const deactivateMutation = useDeactivateEmployee();

  const attendanceQuery = useApiQuery({
    queryKey: ["attendance", employeeId],
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<PaginatedResponse<AttendanceRecord>>>(
        "/attendance",
        { params: { employee_id: employeeId, page: 1, page_size: 20 } },
      );
      return data.data;
    },
    enabled: tab === "attendance" && Boolean(employeeId),
  });

  const leaveQuery = useApiQuery({
    queryKey: ["leave", employeeId],
    queryFn: async () => {
      const { data } = await api.get<SuccessResponse<PaginatedResponse<LeaveHistoryItem>>>(
        "/leave",
        { params: { employee_id: employeeId, page: 1, page_size: 20 } },
      );
      return data.data;
    },
    enabled: tab === "leave" && Boolean(employeeId),
  });

  const performanceQuery = useApiQuery({
    queryKey: ["performance-history", employeeId],
    queryFn: async () => {
      const { data } = await api.get<
        SuccessResponse<PaginatedResponse<PerformanceHistoryItem>>
      >(`/performance/employees/${employeeId}/history`, {
        params: { page: 1, page_size: 20 },
      });
      return data.data;
    },
    enabled: tab === "performance" && Boolean(employeeId),
  });

  if (employeeQuery.isLoading) {
    return <LoadingSpinner label="Loading employee..." />;
  }

  const employee = employeeQuery.data;
  if (!employee) {
    return <p className="text-sm text-muted-foreground">Employee not found.</p>;
  }

  const attendanceColumns: DataTableColumn<AttendanceRecord>[] = [
    { key: "date", header: "Date", render: (row) => row.attendance_date },
    { key: "status", header: "Status", render: (row) => row.status_name },
    { key: "in", header: "Check in", render: (row) => row.check_in_time ?? "—" },
    { key: "out", header: "Check out", render: (row) => row.check_out_time ?? "—" },
  ];

  const leaveColumns: DataTableColumn<LeaveHistoryItem>[] = [
    { key: "type", header: "Type", render: (row) => row.leave_type_name ?? row.leave_type_id },
    { key: "dates", header: "Dates", render: (row) => `${row.start_date} → ${row.end_date}` },
    { key: "status", header: "Status", render: (row) => row.status },
  ];

  const performanceColumns: DataTableColumn<PerformanceHistoryItem>[] = [
    { key: "cycle", header: "Cycle", render: (row) => row.cycle.name },
    { key: "rating", header: "Rating", render: (row) => row.rating },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={employee.full_name}
        description={`${employee.employee_code} · ${employee.designation?.title ?? "No designation"}`}
        action={
          canEdit ? (
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => setShowEdit(true)}>
                Edit
              </Button>
              {canDeactivate ? (
                <Button type="button" variant="destructive" onClick={() => setShowDeactivate(true)}>
                  Deactivate
                </Button>
              ) : null}
            </div>
          ) : null
        }
      />

      <div className="flex flex-wrap gap-2">
        {(["profile", "attendance", "leave", "performance"] as Tab[]).map((item) => (
          <Button
            key={item}
            type="button"
            variant={tab === item ? "default" : "outline"}
            onClick={() => setTab(item)}
          >
            {item.charAt(0).toUpperCase() + item.slice(1)}
          </Button>
        ))}
      </div>

      {tab === "profile" ? (
        <div className="grid gap-4 rounded-xl border bg-card p-4 sm:grid-cols-2">
          <Field label="Email" value={employee.email} />
          <Field label="Phone" value={employee.phone ?? "—"} />
          <Field label="Department" value={employee.department?.name ?? "—"} />
          <Field label="Designation" value={employee.designation?.title ?? "—"} />
          <Field label="Status" value={employee.employment_status?.name ?? "—"} />
          <Field label="Manager" value={employee.manager?.name ?? "—"} />
          <Field label="Join date" value={employee.join_date} />
          {canEdit ? <Field label="Salary" value={employee.salary?.toString() ?? "—"} /> : null}
        </div>
      ) : null}

      {tab === "attendance" ? (
        <DataTable
          columns={attendanceColumns}
          rows={attendanceQuery.data?.items ?? []}
          isLoading={attendanceQuery.isLoading}
          emptyTitle="No attendance records"
        />
      ) : null}

      {tab === "leave" ? (
        <DataTable
          columns={leaveColumns}
          rows={leaveQuery.data?.items ?? []}
          isLoading={leaveQuery.isLoading}
          emptyTitle="No leave requests"
        />
      ) : null}

      {tab === "performance" ? (
        <div className="space-y-4">
          <Link
            href={`/hr/employees/${employeeId}/performance`}
            className="inline-flex h-8 items-center rounded-lg border px-2.5 text-sm hover:bg-muted"
          >
            View full performance history
          </Link>
          <DataTable
            columns={performanceColumns}
            rows={performanceQuery.data?.items ?? []}
            isLoading={performanceQuery.isLoading}
            getRowKey={(row) => row.review_id}
            emptyTitle="No performance history"
          />
        </div>
      ) : null}

      {showEdit ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border bg-background p-6">
            <h2 className="mb-4 text-lg font-semibold">Edit employee</h2>
            <EmployeeForm
              mode="edit"
              initial={employee}
              showSalary={canEdit}
              isSubmitting={updateMutation.isPending}
              onCancel={() => setShowEdit(false)}
              onSubmit={async (values) => {
                await updateMutation.mutateAsync(values);
                toast.success("Employee updated.");
                setShowEdit(false);
              }}
            />
          </div>
        </div>
      ) : null}

      {showDeactivate ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <ConfirmDialog
            title="Deactivate employee"
            description={`This will deactivate ${employee.full_name}. This action cannot be undone from the UI.`}
            confirmText="Deactivate"
            onCancel={() => setShowDeactivate(false)}
            onConfirm={async () => {
              try {
                await deactivateMutation.mutateAsync(employee.id);
                toast.success("Employee deactivated.");
                setShowDeactivate(false);
              } catch (err) {
                const message = axios.isAxiosError<ErrorResponse>(err)
                  ? err.response?.data?.message
                  : "Unable to deactivate employee.";
                toast.error(message ?? "Unable to deactivate employee.");
              }
            }}
          />
        </div>
      ) : null}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm">{value}</p>
    </div>
  );
}
