"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { EmployeeForm } from "@/components/employees/employee-form";
import { Button } from "@/components/ui/button";
import { useApiQuery } from "@/hooks/use-api-query";
import { useCreateEmployee, useEmployees } from "@/hooks/use-employees";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import {
  listDepartments,
  listDesignations,
  listEmploymentStatuses,
} from "@/services/organization.service";
import type { Employee } from "@/types/api";

export default function EmployeeListPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const { hasRole } = useAuth();
  const canManage = hasRole("hr_manager") || hasRole("system_administrator");
  const [showCreate, setShowCreate] = useState(false);

  const filters = useMemo(
    () => ({
      search: searchParams.get("search") || undefined,
      department_id: searchParams.get("department_id") || undefined,
      designation_id: searchParams.get("designation_id") || undefined,
      status: searchParams.get("status") || undefined,
      page: Number(searchParams.get("page") || "1"),
      page_size: Number(searchParams.get("page_size") || "20"),
    }),
    [searchParams],
  );

  const employeesQuery = useEmployees(filters);
  const createMutation = useCreateEmployee();

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
      router.replace(`/hr/employees?${params.toString()}`);
    },
    [router, searchParams],
  );

  const columns: DataTableColumn<Employee>[] = [
    { key: "name", header: "Name", render: (row) => row.full_name },
    { key: "code", header: "Code", render: (row) => row.employee_code },
    { key: "department", header: "Department", render: (row) => row.department?.name ?? "—" },
    { key: "designation", header: "Designation", render: (row) => row.designation?.title ?? "—" },
    { key: "status", header: "Status", render: (row) => row.employment_status?.name ?? "—" },
    { key: "join_date", header: "Join date", render: (row) => row.join_date },
  ];

  const pagination = employeesQuery.data?.pagination;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Employees"
        description="Manage employee records, assignments, and employment details."
        action={
          canManage ? (
            <Button type="button" onClick={() => setShowCreate(true)}>
              Add Employee
            </Button>
          ) : null
        }
      />

      <div className="grid gap-3 rounded-lg border bg-card p-4 sm:grid-cols-2 lg:grid-cols-4">
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Search</span>
          <input
            className="h-9 rounded-lg border bg-background px-3"
            defaultValue={filters.search ?? ""}
            placeholder="Name, email, code..."
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                updateParams({ search: (event.target as HTMLInputElement).value || null, page: "1" });
              }
            }}
          />
        </label>
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
          <span className="font-medium">Status</span>
          <select
            className="h-9 rounded-lg border bg-background px-3"
            value={filters.status ?? ""}
            onChange={(event) => updateParams({ status: event.target.value || null, page: "1" })}
          >
            <option value="">All</option>
            {(statusesQuery.data ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <DataTable
        columns={columns}
        rows={employeesQuery.data?.items ?? []}
        isLoading={employeesQuery.isLoading}
        getRowKey={(row) => row.id}
        onRowClick={(row) => router.push(`/hr/employees/${row.id}`)}
        emptyTitle="No employees found"
        emptyDescription="Try adjusting filters or add a new employee."
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

      {showCreate ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border bg-background p-6">
            <h2 className="mb-4 text-lg font-semibold">Add employee</h2>
            <EmployeeForm
              mode="create"
              showSalary={canManage}
              isSubmitting={createMutation.isPending}
              onCancel={() => setShowCreate(false)}
              onSubmit={async (values) => {
                await createMutation.mutateAsync(values as Parameters<typeof createMutation.mutateAsync>[0]);
                toast.success("Employee created.");
                setShowCreate(false);
              }}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
