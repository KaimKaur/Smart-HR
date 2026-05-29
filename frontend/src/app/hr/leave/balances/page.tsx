"use client";

import { useMemo, useState } from "react";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { useApiQuery } from "@/hooks/use-api-query";
import { useEmployees } from "@/hooks/use-employees";
import { useInitializeLeaveBalances } from "@/hooks/use-leave";
import { useToast } from "@/hooks/use-toast";
import { getManyLeaveBalances } from "@/services/leave.service";
import type { LeaveBalanceResponse } from "@/types/api";

type BalanceRow = {
  employee_id: string;
  employee_name: string;
  leave_summary: string;
};

export default function HrLeaveBalancesPage() {
  const toast = useToast();
  const [showInitializeConfirm, setShowInitializeConfirm] = useState(false);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const [adjustmentForm, setAdjustmentForm] = useState({
    employee_id: "",
    leave_type_id: "",
    new_balance: "",
  });
  const initializeMutation = useInitializeLeaveBalances();

  const employeesQuery = useEmployees({ page: 1, page_size: 50 });
  const balancesQuery = useApiQuery({
    queryKey: ["leave", "balances", "all-employees", employeesQuery.data?.items.map((item) => item.id)],
    queryFn: () => getManyLeaveBalances((employeesQuery.data?.items ?? []).map((item) => item.id)),
    enabled: Boolean(employeesQuery.data?.items.length),
  });

  const employeeNameById = useMemo(
    () => new Map((employeesQuery.data?.items ?? []).map((employee) => [employee.id, employee.full_name])),
    [employeesQuery.data?.items],
  );

  const rows: BalanceRow[] = useMemo(
    () =>
      (balancesQuery.data ?? []).map((balance: LeaveBalanceResponse) => ({
        employee_id: balance.employee_id,
        employee_name: employeeNameById.get(balance.employee_id) ?? balance.employee_id,
        leave_summary: balance.balances
          .map((item) => `${item.leave_type}: ${Number(item.current_balance).toFixed(1)}/${item.annual_allocation}`)
          .join(" | "),
      })),
    [balancesQuery.data, employeeNameById],
  );

  const columns: DataTableColumn<BalanceRow>[] = [
    { key: "employee", header: "Employee", render: (row) => row.employee_name },
    { key: "balances", header: "Balances", render: (row) => row.leave_summary || "—" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Leave balances" description="Initialize annual leave balances and review employee totals." />

      <section className="grid gap-4 rounded-xl border bg-card p-4 lg:grid-cols-2">
        <div className="space-y-3">
          <h2 className="text-base font-semibold">Initialize balances for new year</h2>
          <p className="text-sm text-muted-foreground">
            This creates missing leave balances from leave type annual allocations.
          </p>
          <Button type="button" onClick={() => setShowInitializeConfirm(true)}>
            Initialize for all employees
          </Button>
        </div>
        <div className="space-y-3">
          <h2 className="text-base font-semibold">Per-employee initialization</h2>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Employee</span>
            <select
              className="h-9 rounded-lg border px-3"
              value={selectedEmployeeId}
              onChange={(event) => setSelectedEmployeeId(event.target.value)}
            >
              <option value="">Select employee</option>
              {(employeesQuery.data?.items ?? []).map((employee) => (
                <option key={employee.id} value={employee.id}>
                  {employee.full_name}
                </option>
              ))}
            </select>
          </label>
          <Button
            type="button"
            variant="outline"
            disabled={!selectedEmployeeId || initializeMutation.isPending}
            onClick={async () => {
              await initializeMutation.mutateAsync({
                employee_id: selectedEmployeeId,
                all_employees: false,
              });
              toast.success("Leave balances initialized for selected employee.");
              await balancesQuery.refetch();
            }}
          >
            Initialize selected employee
          </Button>
        </div>
      </section>

      <section className="space-y-2 rounded-xl border bg-card p-4">
        <h2 className="text-base font-semibold">Manual adjustment</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Employee</span>
            <select
              className="h-9 rounded-lg border px-3"
              value={adjustmentForm.employee_id}
              onChange={(event) =>
                setAdjustmentForm((current) => ({ ...current, employee_id: event.target.value }))
              }
            >
              <option value="">Select employee</option>
              {(employeesQuery.data?.items ?? []).map((employee) => (
                <option key={employee.id} value={employee.id}>
                  {employee.full_name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Leave type</span>
            <input
              className="h-9 rounded-lg border px-3"
              placeholder="Leave type id"
              value={adjustmentForm.leave_type_id}
              onChange={(event) =>
                setAdjustmentForm((current) => ({ ...current, leave_type_id: event.target.value }))
              }
            />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">New balance</span>
            <input
              type="number"
              className="h-9 rounded-lg border px-3"
              value={adjustmentForm.new_balance}
              onChange={(event) =>
                setAdjustmentForm((current) => ({ ...current, new_balance: event.target.value }))
              }
            />
          </label>
        </div>
        <Button type="button" variant="outline" disabled>
          Save adjustment (API unavailable)
        </Button>
        <p className="text-sm text-muted-foreground">
          Manual adjustment endpoint is not exposed by the current backend leave API; initialization endpoints are
          implemented and wired.
        </p>
      </section>

      <DataTable
        columns={columns}
        rows={rows}
        isLoading={employeesQuery.isLoading || balancesQuery.isLoading}
        getRowKey={(row) => row.employee_id}
        emptyTitle="No balances found"
      />

      {showInitializeConfirm ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <ConfirmDialog
            title="Initialize all leave balances"
            description="Proceed with annual balance initialization for all employees?"
            confirmText="Initialize"
            onCancel={() => setShowInitializeConfirm(false)}
            onConfirm={async () => {
              await initializeMutation.mutateAsync({ all_employees: true });
              toast.success("Leave balances initialized.");
              setShowInitializeConfirm(false);
              await balancesQuery.refetch();
            }}
          />
        </div>
      ) : null}
    </div>
  );
}
