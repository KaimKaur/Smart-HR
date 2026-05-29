"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { RecommendationBadge } from "@/components/recruitment/recommendation-badge";
import { Button } from "@/components/ui/button";
import {
  useCandidates,
  useOverrideAI,
  useRejectCandidate,
  useShortlistCandidate,
} from "@/hooks/use-candidates";
import { useToast } from "@/hooks/use-toast";
import type { JobCandidateRow } from "@/types/api";

export default function JobCandidatesPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();

  const filters = useMemo(
    () => ({
      status: searchParams.get("status") || undefined,
      page: Number(searchParams.get("page") || "1"),
      page_size: 20,
      sort_by: "ai_score",
      sort_order: "desc" as const,
    }),
    [searchParams],
  );

  const candidatesQuery = useCandidates(params.id, filters);
  const shortlistMutation = useShortlistCandidate();
  const rejectMutation = useRejectCandidate();
  const overrideMutation = useOverrideAI();

  const updateStatus = (status: string | null) => {
    const next = new URLSearchParams(searchParams.toString());
    if (!status) next.delete("status");
    else next.set("status", status);
    next.set("page", "1");
    router.replace(`/recruiter/jobs/${params.id}/candidates?${next.toString()}`);
  };

  const columns: DataTableColumn<JobCandidateRow>[] = [
    { key: "name", header: "Name", render: (row) => row.full_name },
    { key: "email", header: "Email", render: (row) => row.email },
    {
      key: "score",
      header: "AI score",
      render: (row) => {
        const score = Number(row.ai_score ?? 0);
        return (
          <div className="min-w-28">
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-primary" style={{ width: `${Math.min(score, 100)}%` }} />
            </div>
            <span className="text-xs text-muted-foreground">{score || "—"}</span>
          </div>
        );
      },
    },
    { key: "ranking", header: "Ranking", render: (row) => row.ranking ?? "—" },
    {
      key: "recommendation",
      header: "Recommendation",
      render: (row) => <RecommendationBadge recommendation={row.recommendation} />,
    },
    {
      key: "status",
      header: "Status",
      render: (row) => <StatusBadge status={row.application_status} />,
    },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex flex-wrap gap-1">
          <Button asChild size="sm" variant="outline">
            <Link href={`/recruiter/candidates/${row.candidate_id}?applicationId=${row.application_id}&jobId=${params.id}`}>
              View
            </Link>
          </Button>
          <Button
            size="sm"
            type="button"
            onClick={async () => {
              await shortlistMutation.mutateAsync(row.application_id);
              toast.success("Candidate shortlisted.");
            }}
          >
            Shortlist
          </Button>
          <Button
            size="sm"
            type="button"
            variant="destructive"
            onClick={async () => {
              await rejectMutation.mutateAsync(row.application_id);
              toast.success("Candidate rejected.");
            }}
          >
            Reject
          </Button>
          <Button
            size="sm"
            type="button"
            variant="outline"
            onClick={async () => {
              await overrideMutation.mutateAsync({
                applicationId: row.application_id,
                status: "shortlisted",
                remarks: "Manual override from candidate list",
              });
              toast.success("AI decision overridden.");
            }}
          >
            Override
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Job candidates"
        description="Review applicants sorted by AI score."
        action={
          <Button asChild variant="outline">
            <Link href={`/recruiter/jobs/${params.id}/ranking`}>View ranking</Link>
          </Button>
        }
      />

      <div className="flex flex-wrap gap-2">
        {["all", "applied", "shortlisted", "rejected", "interview_scheduled"].map((status) => (
          <Button
            key={status}
            type="button"
            variant={(filters.status ?? "all") === status ? "default" : "outline"}
            onClick={() => updateStatus(status === "all" ? null : status)}
          >
            {status.replaceAll("_", " ")}
          </Button>
        ))}
      </div>

      <DataTable
        columns={columns}
        rows={candidatesQuery.data?.items ?? []}
        isLoading={candidatesQuery.isLoading}
        getRowKey={(row) => row.application_id}
        emptyTitle="No candidates"
      />
    </div>
  );
}
