"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { RecommendationBadge } from "@/components/recruitment/recommendation-badge";
import { Button } from "@/components/ui/button";
import { useApiQuery } from "@/hooks/use-api-query";
import { useRejectCandidate, useShortlistCandidate } from "@/hooks/use-candidates";
import { useToast } from "@/hooks/use-toast";
import { getJobCandidateRanking } from "@/services/job.service";
import { bulkShortlistApplications } from "@/services/candidate.service";
import type { JobCandidateRow } from "@/types/api";

export default function CandidateRankingPage() {
  const params = useParams<{ id: string }>();
  const toast = useToast();
  const [selected, setSelected] = useState<string[]>([]);

  const rankingQuery = useApiQuery({
    queryKey: ["job-ranking", params.id],
    queryFn: () => getJobCandidateRanking(params.id, 1, 100),
    enabled: Boolean(params.id),
  });

  const shortlistMutation = useShortlistCandidate();
  const rejectMutation = useRejectCandidate();

  const rows = useMemo(
    () =>
      (rankingQuery.data?.items ?? []).map((row, index) => ({
        ...row,
        position: index + 1,
      })),
    [rankingQuery.data?.items],
  );

  const columns: DataTableColumn<JobCandidateRow & { position: number }>[] = [
    {
      key: "select",
      header: "",
      render: (row) => (
        <input
          type="checkbox"
          checked={selected.includes(row.application_id)}
          onChange={(event) => {
            setSelected((current) =>
              event.target.checked
                ? [...current, row.application_id]
                : current.filter((id) => id !== row.application_id),
            );
          }}
        />
      ),
    },
    { key: "position", header: "#", render: (row) => row.position },
    {
      key: "name",
      header: "Name",
      render: (row) => (
        <span className="inline-flex items-center gap-2">
          {row.full_name}
          {row.recruiter_override ? <span title="Manual override">⚑</span> : null}
        </span>
      ),
    },
    { key: "score", header: "Score", render: (row) => row.ai_score ?? row.score ?? "—" },
    {
      key: "matched",
      header: "Matched skills",
      render: (row) => (Array.isArray(row.matched_skills) ? row.matched_skills.length : "—"),
    },
    {
      key: "recommendation",
      header: "Recommendation",
      render: (row) => <RecommendationBadge recommendation={row.recommendation} />,
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
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Candidate ranking"
        description="AI-ranked candidates for this job."
        action={
          <div className="flex gap-2">
            <Button
              type="button"
              disabled={!selected.length}
              onClick={async () => {
                await bulkShortlistApplications(selected);
                toast.success("Selected candidates shortlisted.");
                setSelected([]);
                await rankingQuery.refetch();
              }}
            >
              Bulk shortlist ({selected.length})
            </Button>
            <Button asChild variant="outline">
              <Link href={`/recruiter/jobs/${params.id}/candidates`}>Back to candidates</Link>
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        rows={rows}
        isLoading={rankingQuery.isLoading}
        getRowKey={(row) => row.application_id}
        emptyTitle="No ranked candidates"
      />
    </div>
  );
}
