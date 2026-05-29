'use client'

"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StarRating } from "@/components/performance/star-rating";
import { useCycles, useTeamPerformance } from "@/hooks/use-performance";
import type { EmployeePerformanceSummary } from "@/types/api";

export default function ManagerTeamPerformancePage() {
  const router = useRouter();
  const [cycleId, setCycleId] = useState("");
  const [page, setPage] = useState(1);
  const cyclesQuery = useCycles(1, 100);
  const teamQuery = useTeamPerformance(cycleId || undefined, page, 20);

  const rows = useMemo(
    () =>
      [...(teamQuery.data?.items ?? [])].sort((a, b) => b.rating - a.rating),
    [teamQuery.data?.items],
  );

  const averageTeamRating = useMemo(() => {
    if (!rows.length) return null;
    return rows.reduce((sum, row) => sum + row.rating, 0) / rows.length;
  }, [rows]);

  const columns: DataTableColumn<EmployeePerformanceSummary>[] = [
    { key: "employee", header: "Employee", render: (row) => row.employee.full_name },
    { key: "department", header: "Department", render: (row) => row.employee.department_name ?? "—" },
    { key: "cycle", header: "Cycle", render: (row) => row.cycle.name },
    {
      key: "rating",
      header: "Rating",
      render: (row) => <StarRating rating={row.rating} size="sm" />,
    },
    {
      key: "score",
      header: "Avg metric score",
      render: (row) =>
        row.average_metric_score != null ? `${row.average_metric_score.toFixed(1)}%` : "—",
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team performance"
        description={
          averageTeamRating != null
            ? `Average team rating: ${averageTeamRating.toFixed(1)} / 5`
            : "Review direct report performance by cycle."
        }
      />

      <label className="grid max-w-sm gap-1 text-sm">
        <span className="font-medium">Cycle filter</span>
        <select
          className="h-9 rounded-lg border px-3"
          value={cycleId}
          onChange={(event) => {
            setCycleId(event.target.value);
            setPage(1);
          }}
        >
          <option value="">All cycles</option>
          {(cyclesQuery.data?.items ?? []).map((cycle) => (
            <option key={cycle.id} value={cycle.id}>
              {cycle.name}
            </option>
          ))}
        </select>
      </label>

      <DataTable
        columns={columns}
        rows={rows}
        isLoading={teamQuery.isLoading}
        getRowKey={(row) => row.review_id}
        emptyTitle="No team reviews"
        onRowClick={(row) => router.push(`/hr/employees/${row.employee.id}`)}
      />

      {teamQuery.data?.pagination ? (
        <div className="flex justify-end gap-2">
          <button
            type="button"
            className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
            disabled={page <= 1}
            onClick={() => setPage((v) => v - 1)}
          >
            Previous
          </button>
          <button
            type="button"
            className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
            disabled={page >= teamQuery.data.pagination.total_pages}
            onClick={() => setPage((v) => v + 1)}
          >
            Next
          </button>
        </div>
      ) : null}
    </div>
  );
}
