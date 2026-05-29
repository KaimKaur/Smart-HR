"use client";

import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { LeaveApprovalDialog } from "@/components/leave/leave-approval-dialog";
import { usePendingApprovals } from "@/hooks/use-leave";
import type { LeaveRequest } from "@/types/api";

export default function LeaveApprovalsPage() {
  const [page, setPage] = useState(1);
  const [selectedRequest, setSelectedRequest] = useState<LeaveRequest | null>(null);
  const pendingQuery = usePendingApprovals(page, 20);

  const rows = useMemo(
    () =>
      [...(pendingQuery.data?.items ?? [])].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
    [pendingQuery.data?.items],
  );

  const columns: DataTableColumn<LeaveRequest>[] = [
    { key: "employee", header: "Employee", render: (row) => row.employee_name },
    { key: "type", header: "Leave type", render: (row) => row.leave_type_name },
    { key: "start", header: "Start", render: (row) => row.start_date },
    { key: "end", header: "End", render: (row) => row.end_date },
    { key: "requested", header: "Requested at", render: (row) => new Date(row.created_at).toLocaleString() },
    {
      key: "action",
      header: "",
      render: (row) => (
        <button
          type="button"
          className="rounded-md border px-3 py-1 text-sm hover:bg-muted"
          onClick={() => setSelectedRequest(row)}
        >
          Review
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leave approvals"
        description="Review pending leave requests and record approval remarks."
      />
      <DataTable
        columns={columns}
        rows={rows}
        isLoading={pendingQuery.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No pending requests"
      />
      {pendingQuery.data?.pagination ? (
        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
            disabled={page <= 1}
            onClick={() => setPage((value) => value - 1)}
          >
            Previous
          </button>
          <button
            type="button"
            className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
            disabled={page >= pendingQuery.data.pagination.total_pages}
            onClick={() => setPage((value) => value + 1)}
          >
            Next
          </button>
        </div>
      ) : null}

      {selectedRequest ? (
        <LeaveApprovalDialog
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
          onSuccess={() => void pendingQuery.refetch()}
        />
      ) : null}
    </div>
  );
}
