"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { InterviewScheduleForm } from "@/components/recruitment/interview-schedule-form";
import { Button } from "@/components/ui/button";
import { useInterviews, useUpdateInterview } from "@/hooks/use-interviews";
import { useToast } from "@/hooks/use-toast";
import type { Interview } from "@/types/api";

export default function InterviewsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [scheduleApplicationId, setScheduleApplicationId] = useState<string | null>(null);

  const statusFilter = searchParams.get("status") ?? "all";
  const filters = useMemo(
    () => ({
      status: statusFilter === "all" ? undefined : statusFilter,
      page: Number(searchParams.get("page") || "1"),
      page_size: 20,
    }),
    [searchParams, statusFilter],
  );

  const interviewsQuery = useInterviews(filters);
  const updateMutation = useUpdateInterview();

  const setStatusFilter = (status: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (status === "all") params.delete("status");
    else params.set("status", status);
    router.replace(`/recruiter/interviews?${params.toString()}`);
  };

  const columns: DataTableColumn<Interview>[] = [
    { key: "candidate", header: "Candidate", render: (row) => row.candidate_name },
    { key: "job", header: "Job", render: (row) => row.job_title },
    { key: "when", header: "Scheduled", render: (row) => new Date(row.scheduled_at).toLocaleString() },
    { key: "interviewer", header: "Interviewer", render: (row) => row.interviewer_name ?? "—" },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
    {
      key: "actions",
      header: "Update status",
      render: (row) => (
        <select
          className="h-8 rounded-lg border px-2 text-sm"
          value={row.status}
          onChange={async (event) => {
            await updateMutation.mutateAsync({
              id: row.id,
              payload: { status: event.target.value as Interview["status"] },
            });
            toast.success("Interview status updated.");
          }}
        >
          <option value="scheduled">Scheduled</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="no_show">No show</option>
        </select>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Interviews"
        description="Upcoming and past interview schedules."
        action={
          <Button type="button" onClick={() => setScheduleApplicationId("")}>
            Schedule interview
          </Button>
        }
      />

      <div className="flex flex-wrap gap-2">
        {["all", "scheduled", "completed", "cancelled"].map((status) => (
          <Button
            key={status}
            type="button"
            variant={statusFilter === status ? "default" : "outline"}
            onClick={() => setStatusFilter(status)}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Button>
        ))}
      </div>

      <DataTable
        columns={columns}
        rows={interviewsQuery.data?.items ?? []}
        isLoading={interviewsQuery.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No interviews found"
      />

      {scheduleApplicationId !== null ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-xl border bg-background p-6">
            <h2 className="mb-4 text-lg font-semibold">Schedule interview</h2>
            <label className="mb-4 grid gap-1 text-sm">
              Application ID
              <input
                className="h-9 rounded-lg border px-3"
                value={scheduleApplicationId}
                onChange={(event) => setScheduleApplicationId(event.target.value)}
                placeholder="Paste application UUID"
              />
            </label>
            {scheduleApplicationId ? (
              <InterviewScheduleForm
                applicationId={scheduleApplicationId}
                onCancel={() => setScheduleApplicationId(null)}
                onSuccess={() => {
                  setScheduleApplicationId(null);
                  void interviewsQuery.refetch();
                }}
              />
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
