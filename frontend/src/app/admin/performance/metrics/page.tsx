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
  useCreateMetric,
  useDeleteMetric,
  useMetrics,
  useUpdateMetric,
} from "@/hooks/use-performance";
import { useToast } from "@/hooks/use-toast";
import { performanceMetricSchema } from "@/lib/validations";
import type { ErrorResponse, PerformanceMetric } from "@/types/api";

type MetricFormValues = z.infer<typeof performanceMetricSchema>;

export default function PerformanceMetricsPage() {
  const toast = useToast();
  const [editingMetric, setEditingMetric] = useState<PerformanceMetric | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<PerformanceMetric | null>(null);
  const metricsQuery = useMetrics(1, 100);
  const createMutation = useCreateMetric();
  const updateMutation = useUpdateMetric();
  const deleteMutation = useDeleteMetric();

  const createForm = useForm<MetricFormValues>({
    resolver: zodResolver(performanceMetricSchema),
    defaultValues: { name: "", description: "" },
  });

  const columns: DataTableColumn<PerformanceMetric>[] = [
    { key: "name", header: "Name", render: (row) => row.name },
    { key: "description", header: "Description", render: (row) => row.description ?? "—" },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex gap-2">
          <Button type="button" size="sm" variant="outline" onClick={() => setEditingMetric(row)}>
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
      <PageHeader title="Performance metrics" description="Manage metrics used in performance reviews." />

      <form
        className="grid gap-4 rounded-xl border bg-card p-4 sm:grid-cols-2"
        onSubmit={createForm.handleSubmit(async (values) => {
          await createMutation.mutateAsync(values);
          toast.success("Metric created.");
          createForm.reset();
          await metricsQuery.refetch();
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
            Add metric
          </Button>
        </div>
      </form>

      <DataTable
        columns={columns}
        rows={metricsQuery.data?.items ?? []}
        isLoading={metricsQuery.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No metrics"
      />

      {editingMetric ? (
        <MetricEditDialog
          metric={editingMetric}
          isSubmitting={updateMutation.isPending}
          onCancel={() => setEditingMetric(null)}
          onSave={async (values) => {
            await updateMutation.mutateAsync({ metricId: editingMetric.id, payload: values });
            toast.success("Metric updated.");
            setEditingMetric(null);
            await metricsQuery.refetch();
          }}
        />
      ) : null}

      {deleteTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <ConfirmDialog
            title="Delete metric"
            description={`Delete "${deleteTarget.name}"? Deletion is blocked if scores exist.`}
            confirmText="Delete"
            onCancel={() => setDeleteTarget(null)}
            onConfirm={async () => {
              try {
                await deleteMutation.mutateAsync(deleteTarget.id);
                toast.success("Metric deleted.");
                setDeleteTarget(null);
                await metricsQuery.refetch();
              } catch (error) {
                if (axios.isAxiosError<ErrorResponse>(error) && error.response?.status === 409) {
                  toast.error(error.response.data.message || "Cannot delete metric with existing scores.");
                  return;
                }
                toast.error("Unable to delete metric.");
              }
            }}
          />
        </div>
      ) : null}
    </div>
  );
}

function MetricEditDialog({
  metric,
  isSubmitting,
  onCancel,
  onSave,
}: {
  metric: PerformanceMetric;
  isSubmitting?: boolean;
  onCancel: () => void;
  onSave: (values: MetricFormValues) => Promise<void>;
}) {
  const form = useForm<MetricFormValues>({
    resolver: zodResolver(performanceMetricSchema),
    defaultValues: {
      name: metric.name,
      description: metric.description ?? "",
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        className="w-full max-w-lg space-y-4 rounded-xl border bg-background p-6"
        onSubmit={form.handleSubmit(onSave)}
      >
        <h2 className="text-lg font-semibold">Edit metric</h2>
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
