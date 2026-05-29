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
import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import { useToast } from "@/hooks/use-toast";
import { departmentSchema } from "@/lib/validations";
import {
  createDepartment,
  deleteDepartment,
  listDepartments,
  updateDepartment,
} from "@/services/organization.service";
import type { Department, ErrorResponse } from "@/types/api";

type DepartmentFormValues = z.infer<typeof departmentSchema>;

export default function DepartmentsPage() {
  const toast = useToast();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Department | null>(null);

  const departmentsQuery = useApiQuery({
    queryKey: ["departments", "manage"],
    queryFn: () => listDepartments(1, 100),
  });

  const createMutation = useApiMutation({
    mutationFn: createDepartment,
    onSuccess: async () => {
      await departmentsQuery.refetch();
      toast.success("Department created.");
    },
  });

  const updateMutation = useApiMutation({
    mutationFn: ({ id, payload }: { id: string; payload: DepartmentFormValues }) =>
      updateDepartment(id, payload),
    onSuccess: async () => {
      await departmentsQuery.refetch();
      toast.success("Department updated.");
      setEditingId(null);
    },
  });

  const deleteMutation = useApiMutation({
    mutationFn: deleteDepartment,
    onSuccess: async () => {
      await departmentsQuery.refetch();
      toast.success("Department deleted.");
      setDeleteTarget(null);
    },
  });

  const createForm = useForm<DepartmentFormValues>({
    resolver: zodResolver(departmentSchema),
    defaultValues: { name: "", description: "" },
  });

  const columns: DataTableColumn<Department>[] = [
    { key: "name", header: "Name", render: (row) => row.name },
    { key: "description", header: "Description", render: (row) => row.description ?? "—" },
    { key: "employees", header: "Employees", render: (row) => row.employee_count },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex gap-2">
          <Button type="button" size="sm" variant="outline" onClick={() => setEditingId(row.id)}>
            Edit
          </Button>
          <Button type="button" size="sm" variant="destructive" onClick={() => setDeleteTarget(row)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  const editingDepartment = departmentsQuery.data?.items.find((d) => d.id === editingId);

  return (
    <div className="space-y-6">
      <PageHeader title="Departments" description="Manage organizational departments." />

      <form
        className="grid gap-4 rounded-xl border bg-card p-4 sm:grid-cols-2"
        onSubmit={createForm.handleSubmit(async (values) => {
          await createMutation.mutateAsync(values);
          createForm.reset();
        })}
      >
        <FormField label="Name" required error={createForm.formState.errors.name?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...createForm.register("name")} />
        </FormField>
        <FormField label="Description" error={createForm.formState.errors.description?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...createForm.register("description")} />
        </FormField>
        <div className="sm:col-span-2">
          <Button type="submit" disabled={createMutation.isPending}>
            Add department
          </Button>
        </div>
      </form>

      <DataTable
        columns={columns}
        rows={departmentsQuery.data?.items ?? []}
        isLoading={departmentsQuery.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No departments"
      />

      {editingDepartment ? (
        <InlineDepartmentEdit
          department={editingDepartment}
          isSubmitting={updateMutation.isPending}
          onCancel={() => setEditingId(null)}
          onSave={async (values) => {
            await updateMutation.mutateAsync({ id: editingDepartment.id, payload: values });
          }}
        />
      ) : null}

      {deleteTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <ConfirmDialog
            title="Delete department"
            description={`Delete "${deleteTarget.name}"? ${deleteTarget.employee_count} employee(s) are assigned. Deletion may be blocked if employees remain.`}
            confirmText="Delete"
            onCancel={() => setDeleteTarget(null)}
            onConfirm={async () => {
              try {
                await deleteMutation.mutateAsync(deleteTarget.id);
              } catch (err) {
                const message = axios.isAxiosError<ErrorResponse>(err)
                  ? err.response?.data?.message
                  : "Unable to delete department.";
                toast.error(message ?? "Unable to delete department.");
              }
            }}
          />
        </div>
      ) : null}
    </div>
  );
}

function InlineDepartmentEdit({
  department,
  isSubmitting,
  onCancel,
  onSave,
}: {
  department: Department;
  isSubmitting?: boolean;
  onCancel: () => void;
  onSave: (values: DepartmentFormValues) => Promise<void>;
}) {
  const form = useForm<DepartmentFormValues>({
    resolver: zodResolver(departmentSchema),
    defaultValues: {
      name: department.name,
      description: department.description ?? "",
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        className="w-full max-w-lg space-y-4 rounded-xl border bg-background p-6"
        onSubmit={form.handleSubmit(onSave)}
      >
        <h2 className="text-lg font-semibold">Edit department</h2>
        <FormField label="Name" required error={form.formState.errors.name?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("name")} />
        </FormField>
        <FormField label="Description" error={form.formState.errors.description?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("description")} />
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
