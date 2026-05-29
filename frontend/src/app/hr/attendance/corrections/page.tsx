"use client";

import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { usePendingCorrections, useReviewCorrection } from "@/hooks/use-attendance";
import { useToast } from "@/hooks/use-toast";
import type { AttendanceCorrection, AttendanceReportRow } from "@/types/api";

type PendingRow = AttendanceCorrection & { record?: AttendanceReportRow };

function daysAgoIso(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().slice(0, 10);
}

export default function HrCorrectionsPage() {
  const toast = useToast();
  const [remarksById, setRemarksById] = useState<Record<string, string>>({});

  const dateFrom = daysAgoIso(30);
  const dateTo = new Date().toISOString().slice(0, 10);

  const pendingQuery = usePendingCorrections(dateFrom, dateTo);
  const reviewMutation = useReviewCorrection();

  const rows = pendingQuery.data ?? [];

  const columns: DataTableColumn<PendingRow>[] = useMemo(
    () => [
      {
        key: "employee",
        header: "Employee",
        render: (row) => row.record?.full_name ?? "—",
      },
      {
        key: "date",
        header: "Date",
        render: (row) => row.record?.attendance_date ?? "—",
      },
      {
        key: "reason",
        header: "Reason",
        render: (row) => row.reason,
      },
      {
        key: "status",
        header: "Status",
        render: (row) => <StatusBadge status={row.correction_status} />,
      },
      {
        key: "remarks",
        header: "Remarks",
        render: (row) => (
          <input
            className="h-8 w-full min-w-40 rounded-lg border px-2 text-sm"
            value={remarksById[row.id] ?? ""}
            onChange={(event) =>
              setRemarksById((current) => ({ ...current, [row.id]: event.target.value }))
            }
            placeholder="Optional remarks"
          />
        ),
      },
      {
        key: "actions",
        header: "Actions",
        render: (row) => (
          <div className="flex gap-1">
            <Button
              size="sm"
              type="button"
              onClick={async () => {
                await reviewMutation.mutateAsync({ correctionId: row.id, status: "approved" });
                toast.success("Correction approved.");
                await pendingQuery.refetch();
              }}
            >
              Approve
            </Button>
            <Button
              size="sm"
              type="button"
              variant="destructive"
              onClick={async () => {
                await reviewMutation.mutateAsync({ correctionId: row.id, status: "rejected" });
                toast.success("Correction rejected.");
                await pendingQuery.refetch();
              }}
            >
              Reject
            </Button>
          </div>
        ),
      },
    ],
    [remarksById, reviewMutation, pendingQuery, toast],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance corrections"
        description="Review and approve pending attendance correction requests."
      />

      <DataTable
        columns={columns}
        rows={rows}
        isLoading={pendingQuery.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No pending corrections"
        emptyDescription="Pending requests from the last 30 days will appear here."
      />
    </div>
  );
}
