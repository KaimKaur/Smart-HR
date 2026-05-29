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
import { designationSchema } from "@/lib/validations";
import {
  createDesignation,
  deleteDesignation,
  listDesignations,
  updateDesignation,
} from "@/services/organization.service";
import type { Designation, ErrorResponse } from "@/types/api";

type DesignationFormValues = z.infer<typeof designationSchema>;

export default function DesignationsPage() {
  const toast = useToast();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Designation | null>(null);

  const designationsQuery = useApiQuery({
    queryKey: ["designations", "manage"],
    queryFn: () => listDesignations(1, 100),
  });

  const createMutation = useApiMutation({
    mutationFn: createDesignation,
    onSuccess: async () => {
      await designationsQuery.refetch();
      toast.success("Designation created.");
    },
  });

  const updateMutation = useApiMutation({
    mutationFn: ({ id, payload }: { id: string; payload: DesignationFormValues }) =>
      updateDesignation(id, payload),
    onSuccess: async () => {
      await designationsQuery.refetch();
      toast.success("Designation updated.");
      setEditingId(null);
    },
  });

  const deleteMutation = useApiMutation({
    mutationFn: deleteDesignation,
    onSuccess: async () => {
      await designationsQuery.refetch();
      toast.success("Designation deleted.");
      setDeleteTarget(null);
    },
  });

  const createForm = useForm<DesignationFormValues>({
    resolver: zodResolver(designationSchema),
    defaultValues: { title: "", description: "" },
  });

  const existingTitles = new Set(
    (designationsQuery.data?.items ?? []).map((item) => item.title.toLowerCase()),
  );

  const columns: DataTableColumn<Designation>[] = [
    { key: "title", header: "Title", render: (row) => row.title },
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

  const editingDesignation = designationsQuery.data?.items.find((d) => d.id === editingId);

  return (
    <div className="space-y-6">
      <PageHeader title="Designations" description="Manage job designations and titles." />

      <form
        className="grid gap-4 rounded-xl border bg-card p-4 sm:grid-cols-2"
        onSubmit={createForm.handleSubmit(async (values) => {
          if (existingTitles.has(values.title.trim().toLowerCase())) {
            createForm.setError("title", { message: "Title must be unique" });
            return;
          }
          await createMutation.mutateAsync(values);
          createForm.reset();
        })}
      >
        <FormField label="Title" required error={createForm.formState.errors.title?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...createForm.register("title")} />
        </FormField>
        <FormField label="Description" error={createForm.formState.errors.description?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...createForm.register("description")} />
        </FormField>
        <div className="sm:col-span-2">
          <Button type="submit" disabled={createMutation.isPending}>
            Add designation
          </Button>
        </div>
      </form>

      <DataTable
        columns={columns}
        rows={designationsQuery.data?.items ?? []}
        isLoading={designationsQuery.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No designations"
      />

      {editingDesignation ? (
        <InlineDesignationEdit
          department={editingDesignation}
          isSubmitting={updateMutation.isPending}
          onCancel={() => setEditingId(null)}
          onSave={async (values) => {
            await updateMutation.mutateAsync({ id: editingDesignation.id, payload: values });
          }}
        />
      ) : null}

      {deleteTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <ConfirmDialog
            title="Delete designation"
            description={`Delete "${deleteTarget.title}"? ${deleteTarget.employee_count} employee(s) are assigned. Deletion may be blocked if employees remain.`}
            confirmText="Delete"
            onCancel={() => setDeleteTarget(null)}
            onConfirm={async () => {
              try {
                await deleteMutation.mutateAsync(deleteTarget.id);
              } catch (err) {
                const message = axios.isAxiosError<ErrorResponse>(err)
                  ? err.response?.data?.message
                  : "Unable to delete designation.";
                toast.error(message ?? "Unable to delete designation.");
              }
            }}
          />
        </div>
      ) : null}
    </div>
  );
}

function InlineDesignationEdit({
  department,
  isSubmitting,
  onCancel,
  onSave,
}: {
  department: Designation;
  isSubmitting?: boolean;
  onCancel: () => void;
  onSave: (values: DesignationFormValues) => Promise<void>;
}) {
  const form = useForm<DesignationFormValues>({
    resolver: zodResolver(designationSchema),
    defaultValues: {
      title: department.title,
      description: department.description ?? "",
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        className="w-full max-w-lg space-y-4 rounded-xl border bg-background p-6"
        onSubmit={form.handleSubmit(onSave)}
      >
        <h2 className="text-lg font-semibold">Edit designation</h2>
        <FormField label="Title" required error={form.formState.errors.title?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("title")} />
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
