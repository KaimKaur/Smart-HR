"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { FormField } from "@/components/common/form-field";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { useCreateCycle, useCycles } from "@/hooks/use-performance";
import { useToast } from "@/hooks/use-toast";
import { performanceCycleSchema } from "@/lib/validations";
import type { PerformanceCycle } from "@/types/api";

type CycleFormValues = z.infer<typeof performanceCycleSchema>;

function cycleGroup(status: PerformanceCycle["status"]): "active" | "past" {
  return status === "active" ? "active" : "past";
}

export default function PerformanceCyclesPage() {
  const toast = useToast();
  const [page, setPage] = useState(1);
  const cyclesQuery = useCycles(page, 20);
  const createMutation = useCreateCycle();

  const form = useForm<CycleFormValues>({
    resolver: zodResolver(performanceCycleSchema),
    defaultValues: { name: "", start_date: "", end_date: "" },
  });

  const { activeCycles, pastCycles } = useMemo(() => {
    const items = cyclesQuery.data?.items ?? [];
    return {
      activeCycles: items.filter((item) => cycleGroup(item.status) === "active"),
      pastCycles: items.filter((item) => cycleGroup(item.status) === "past"),
    };
  }, [cyclesQuery.data?.items]);

  const columns: DataTableColumn<PerformanceCycle>[] = [
    { key: "name", header: "Name", render: (row) => row.name },
    { key: "start", header: "Start", render: (row) => row.start_date },
    { key: "end", header: "End", render: (row) => row.end_date },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Performance cycles" description="Create and manage review cycles." />

      <form
        className="grid gap-4 rounded-xl border bg-card p-4 sm:grid-cols-3"
        onSubmit={form.handleSubmit(async (values) => {
          await createMutation.mutateAsync(values);
          toast.success("Performance cycle created.");
          form.reset();
          await cyclesQuery.refetch();
        })}
      >
        <FormField label="Name" required error={form.formState.errors.name?.message}>
          <input className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("name")} />
        </FormField>
        <FormField label="Start date" required error={form.formState.errors.start_date?.message}>
          <input type="date" className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("start_date")} />
        </FormField>
        <FormField label="End date" required error={form.formState.errors.end_date?.message}>
          <input type="date" className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("end_date")} />
        </FormField>
        <div className="sm:col-span-3">
          <Button type="submit" disabled={createMutation.isPending}>
            Create cycle
          </Button>
        </div>
      </form>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Active cycles</h2>
        <DataTable
          columns={columns}
          rows={activeCycles}
          isLoading={cyclesQuery.isLoading}
          getRowKey={(row) => row.id}
          emptyTitle="No active cycles"
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold">Past cycles</h2>
        <DataTable
          columns={columns}
          rows={pastCycles}
          isLoading={cyclesQuery.isLoading}
          getRowKey={(row) => row.id}
          emptyTitle="No past cycles"
        />
      </section>

      {cyclesQuery.data?.pagination ? (
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" disabled={page <= 1} onClick={() => setPage((v) => v - 1)}>
            Previous
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={page >= cyclesQuery.data.pagination.total_pages}
            onClick={() => setPage((v) => v + 1)}
          >
            Next
          </Button>
        </div>
      ) : null}
    </div>
  );
}
