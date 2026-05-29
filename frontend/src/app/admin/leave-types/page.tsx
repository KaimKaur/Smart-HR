"use client";

import axios from "axios";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { FormField } from "@/components/common/form-field";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import {
  useCreateLeaveType,
  useDeleteLeaveType,
  useLeaveTypes,
  useUpdateLeaveType,
} from "@/hooks/use-leave";
import { useToast } from "@/hooks/use-toast";
import type { ErrorResponse, LeaveType } from "@/types/api";

const leaveTypeSchema = z.object({
  name: z.string().min(1).max(100),
  annual_allocation: z.int().positive("Annual allocation must be a positive integer"),
});

type LeaveTypeValues = z.infer<typeof leaveTypeSchema>;

export default function LeaveTypesPage() {
  const toast = useToast();
  const [editingType, setEditingType] = useState<LeaveType | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<LeaveType | null>(null);
  const leaveTypesQuery = useLeaveTypes();
  const createMutation = useCreateLeaveType();
  const updateMutation = useUpdateLeaveType();
  const deleteMutation = useDeleteLeaveType();

  const createForm = useForm<LeaveTypeValues>({
    resolver: zodResolver(leaveTypeSchema),
    defaultValues: { name: "", annual_allocation: 1 },
  });

  const columns: DataTableColumn<LeaveType>[] = [
    { key: "name", header: "Name", render: (row) => row.name },
    { key: "allocation", header: "Annual allocation", render: (row) => row.annual_allocation },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex gap-2">
          <Button type="button" size="sm" variant="outline" onClick={() => setEditingType(row)}>
            Edit
          </Button>
          <Button type="button" size="sm" variant="destructive" onClick={() => setDeleteTarget(row)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Leave types" description="Create and manage leave types and allocations." />
      <form
        className="grid gap-4 rounded-xl border bg-card p-4 sm:grid-cols-2"
        onSubmit={createForm.handleSubmit(async (values) => {
          await createMutation.mutateAsync(values);
          toast.success("Leave type created.");
          createForm.reset({ name: "", annual_allocation: 1 });
          await leaveTypesQuery.refetch();
        })}
      >
        <FormField label="Name" required error={createForm.formState.errors.name?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...createForm.register("name")} />
        </FormField>
        <FormField
          label="Annual allocation"
          required
          error={createForm.formState.errors.annual_allocation?.message}
        >
          <input
            type="number"
            min={1}
            step={1}
            className="h-9 w-full rounded-lg border px-3 text-sm"
            {...createForm.register("annual_allocation", { valueAsNumber: true })}
          />
        </FormField>
        <div className="sm:col-span-2">
          <Button type="submit" disabled={createMutation.isPending}>
            Add leave type
          </Button>
        </div>
      </form>

      <DataTable
        columns={columns}
        rows={leaveTypesQuery.data ?? []}
        isLoading={leaveTypesQuery.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No leave types"
      />

      {editingType ? (
        <LeaveTypeEditDialog
          leaveType={editingType}
          isSubmitting={updateMutation.isPending}
          onCancel={() => setEditingType(null)}
          onSave={async (values) => {
            await updateMutation.mutateAsync({ leaveTypeId: editingType.id, payload: values });
            toast.success("Leave type updated.");
            setEditingType(null);
            await leaveTypesQuery.refetch();
          }}
        />
      ) : null}

      {deleteTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <ConfirmDialog
            title="Delete leave type"
            description={`Delete "${deleteTarget.name}"? Deletion is blocked if balances already exist.`}
            confirmText="Delete"
            onCancel={() => setDeleteTarget(null)}
            onConfirm={async () => {
              try {
                await deleteMutation.mutateAsync(deleteTarget.id);
                toast.success("Leave type deleted.");
                setDeleteTarget(null);
                await leaveTypesQuery.refetch();
              } catch (error) {
                if (axios.isAxiosError<ErrorResponse>(error) && error.response?.status === 409) {
                  toast.error(error.response.data.message || "Cannot delete leave type with existing balances.");
                  return;
                }
                toast.error("Unable to delete leave type.");
              }
            }}
          />
        </div>
      ) : null}
    </div>
  );
}

function LeaveTypeEditDialog({
  leaveType,
  isSubmitting,
  onCancel,
  onSave,
}: {
  leaveType: LeaveType;
  isSubmitting?: boolean;
  onCancel: () => void;
  onSave: (values: LeaveTypeValues) => Promise<void>;
}) {
  const form = useForm<LeaveTypeValues>({
    resolver: zodResolver(leaveTypeSchema),
    defaultValues: {
      name: leaveType.name,
      annual_allocation: leaveType.annual_allocation,
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        className="w-full max-w-lg space-y-4 rounded-xl border bg-background p-6"
        onSubmit={form.handleSubmit(onSave)}
      >
        <h2 className="text-lg font-semibold">Edit leave type</h2>
        <FormField label="Name" required error={form.formState.errors.name?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("name")} />
        </FormField>
        <FormField label="Annual allocation" required error={form.formState.errors.annual_allocation?.message}>
          <input
            type="number"
            min={1}
            step={1}
            className="h-9 w-full rounded-lg border px-3 text-sm"
            {...form.register("annual_allocation", { valueAsNumber: true })}
          />
        </FormField>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            Save
          </Button>
        </div>
      </form>
    </div>
  );
}
