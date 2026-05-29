"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormField } from "@/components/common/form-field";
import { Button } from "@/components/ui/button";
import { useCreateLeaveRequest, useLeaveTypes } from "@/hooks/use-leave";
import { useToast } from "@/hooks/use-toast";
import { leaveRequestSchema } from "@/lib/validations";
import type { LeaveBalanceItem } from "@/types/api";

type LeaveRequestValues = z.infer<typeof leaveRequestSchema>;

function countWeekdays(startDate: Date, endDate: Date): number {
  const start = new Date(startDate);
  const end = new Date(endDate);
  let count = 0;
  while (start <= end) {
    const day = start.getDay();
    if (day !== 0 && day !== 6) count += 1;
    start.setDate(start.getDate() + 1);
  }
  return count;
}

export function LeaveRequestFormDialog({
  balances,
  onClose,
  onSuccess,
}: {
  balances: LeaveBalanceItem[];
  onClose: () => void;
  onSuccess?: () => void;
}) {
  const toast = useToast();
  const leaveTypesQuery = useLeaveTypes();
  const createMutation = useCreateLeaveRequest();

  const form = useForm<LeaveRequestValues>({
    resolver: zodResolver(leaveRequestSchema),
    defaultValues: {
      leave_type_id: "",
      start_date: "",
      end_date: "",
      reason: "",
    },
  });

  const selectedLeaveTypeId = form.watch("leave_type_id");
  const startDateValue = form.watch("start_date");
  const endDateValue = form.watch("end_date");

  const selectedBalance = useMemo(
    () => balances.find((item) => item.leave_type_id === selectedLeaveTypeId),
    [balances, selectedLeaveTypeId],
  );

  const requestedDays = useMemo(() => {
    if (!startDateValue || !endDateValue) return 0;
    const start = new Date(startDateValue);
    const end = new Date(endDateValue);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) return 0;
    return countWeekdays(start, end);
  }, [startDateValue, endDateValue]);

  const remainingAfterRequest =
    selectedBalance && requestedDays > 0
      ? Number(selectedBalance.current_balance) - requestedDays
      : undefined;
  const hasInsufficientBalance = remainingAfterRequest !== undefined && remainingAfterRequest < 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        className="w-full max-w-lg space-y-4 rounded-xl border bg-background p-6"
        onSubmit={form.handleSubmit(async (values) => {
          if (hasInsufficientBalance) {
            toast.error("Insufficient balance for selected leave type.");
            return;
          }
          await createMutation.mutateAsync({ payload: values });
          toast.success("Leave request submitted.");
          onSuccess?.();
          onClose();
        })}
      >
        <h2 className="text-lg font-semibold">Apply for leave</h2>
        <FormField label="Leave type" required error={form.formState.errors.leave_type_id?.message}>
          <select className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("leave_type_id")}>
            <option value="">Select leave type</option>
            {(leaveTypesQuery.data ?? []).map((type) => (
              <option key={type.id} value={type.id}>
                {type.name}
              </option>
            ))}
          </select>
        </FormField>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Start date" required error={form.formState.errors.start_date?.message}>
            <input type="date" className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("start_date")} />
          </FormField>
          <FormField label="End date" required error={form.formState.errors.end_date?.message}>
            <input type="date" className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("end_date")} />
          </FormField>
        </div>
        <FormField label="Reason" error={form.formState.errors.reason?.message}>
          <textarea
            rows={4}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            placeholder="Optional reason"
            {...form.register("reason")}
          />
        </FormField>
        <div className="rounded-lg border bg-muted/20 p-3 text-sm">
          <p>Requested days: {requestedDays || "—"} (weekends excluded)</p>
          <p>
            Remaining balance:{" "}
            {selectedBalance ? Number(selectedBalance.current_balance).toFixed(1) : "Select a leave type"}
          </p>
          {remainingAfterRequest !== undefined ? (
            <p className={hasInsufficientBalance ? "text-red-600" : "text-green-700"}>
              Balance after request: {remainingAfterRequest.toFixed(1)}
            </p>
          ) : null}
          {hasInsufficientBalance ? (
            <p className="mt-1 text-xs text-red-600">Insufficient balance. Reduce date range or pick another leave type.</p>
          ) : null}
        </div>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Submitting..." : "Submit request"}
          </Button>
        </div>
      </form>
    </div>
  );
}
