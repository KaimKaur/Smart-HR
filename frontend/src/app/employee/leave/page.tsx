"use client";

import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { LeaveRequestFormDialog } from "@/components/leave/leave-request-form-dialog";
import { Button } from "@/components/ui/button";
import { useCancelLeave, useLeaveBalance, useLeaveHistory } from "@/hooks/use-leave";
import { useMarkNotificationRead, useNotifications } from "@/hooks/use-notifications";
import { useToast } from "@/hooks/use-toast";
import type { LeaveRequest } from "@/types/api";

function extractRequestId(text: string): string | null {
  const match = text.match(
    /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/i,
  );
  return match?.[0] ?? null;
}

export default function EmployeeLeavePage() {
  const toast = useToast();
  const searchParams = useSearchParams();
  const [page, setPage] = useState(1);
  const [showRequestDialog, setShowRequestDialog] = useState(false);
  const cancelMutation = useCancelLeave();
  const notificationsQuery = useNotifications({ is_read: false, page: 1, page_size: 20 });
  const markReadMutation = useMarkNotificationRead();
  const highlightedRequestId = searchParams.get("request_id");

  const balanceQuery = useLeaveBalance();
  const historyQuery = useLeaveHistory({ page, page_size: 10 });

  const columns: DataTableColumn<LeaveRequest>[] = useMemo(
    () => [
      { key: "type", header: "Leave type", render: (row) => row.leave_type_name },
      {
        key: "dates",
        header: "Dates",
        render: (row) => `${row.start_date} to ${row.end_date}`,
      },
      {
        key: "status",
        header: "Status",
        render: (row) => (
          <div className="flex items-center gap-2">
            <StatusBadge status={row.status} />
            {row.id === highlightedRequestId ? (
              <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-800">Updated</span>
            ) : null}
          </div>
        ),
      },
      {
        key: "reason",
        header: "Reason",
        render: (row) => row.reason ?? "—",
      },
      {
        key: "actions",
        header: "Actions",
        render: (row) =>
          row.status === "pending" ? (
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={cancelMutation.isPending}
              onClick={async () => {
                await cancelMutation.mutateAsync(row.id);
                toast.success("Leave request cancelled.");
                await historyQuery.refetch();
              }}
            >
              Cancel
            </Button>
          ) : (
            "—"
          ),
      },
    ],
    [cancelMutation, highlightedRequestId, historyQuery, toast],
  );

  const leaveNotifications = useMemo(
    () =>
      (notificationsQuery.data?.items ?? []).filter((item) =>
        `${item.title} ${item.message}`.toLowerCase().includes("leave"),
      ),
    [notificationsQuery.data?.items],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="My leave"
        description="Track balances, submit requests, and monitor approvals."
        action={
          <Button type="button" onClick={() => setShowRequestDialog(true)}>
            Apply for leave
          </Button>
        }
      />

      <section className="space-y-4">
        <h2 className="text-base font-semibold">Leave balances</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(balanceQuery.data?.balances ?? []).map((balance) => (
            <div key={balance.leave_type_id} className="rounded-xl border bg-card p-4">
              <p className="text-sm text-muted-foreground">{balance.leave_type}</p>
              <p className="mt-2 text-2xl font-semibold">{Number(balance.current_balance).toFixed(1)}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Allocated: {balance.annual_allocation} day(s)
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-base font-semibold">Request history</h2>
        <DataTable
          columns={columns}
          rows={historyQuery.data?.items ?? []}
          isLoading={historyQuery.isLoading}
          getRowKey={(row) => row.id}
          emptyTitle="No leave requests"
        />
        {historyQuery.data?.pagination ? (
          <div className="flex items-center justify-end gap-2">
            <Button type="button" variant="outline" disabled={page <= 1} onClick={() => setPage((v) => v - 1)}>
              Previous
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={page >= historyQuery.data.pagination.total_pages}
              onClick={() => setPage((v) => v + 1)}
            >
              Next
            </Button>
          </div>
        ) : null}
      </section>

      <section className="space-y-3 rounded-xl border bg-card p-4">
        <h2 className="text-base font-semibold">Leave notifications</h2>
        {!leaveNotifications.length ? (
          <p className="text-sm text-muted-foreground">No unread leave notifications.</p>
        ) : (
          <ul className="space-y-2">
            {leaveNotifications.map((notification) => {
              const requestId = extractRequestId(`${notification.title} ${notification.message}`);
              const href = requestId ? `/employee/leave?request_id=${requestId}` : "/employee/leave";
              return (
                <li key={notification.id} className="rounded-lg border p-3">
                  <a
                    href={href}
                    className="block"
                    onClick={async () => {
                      await markReadMutation.mutateAsync(notification.id);
                    }}
                  >
                    <p className="text-sm font-medium">{notification.title}</p>
                    <p className="text-sm text-muted-foreground">{notification.message}</p>
                  </a>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {showRequestDialog ? (
        <LeaveRequestFormDialog
          balances={balanceQuery.data?.balances ?? []}
          onClose={() => setShowRequestDialog(false)}
          onSuccess={() => {
            void balanceQuery.refetch();
            void historyQuery.refetch();
          }}
        />
      ) : null}
    </div>
  );
}
