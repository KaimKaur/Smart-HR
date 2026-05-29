"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { AiAnalysisCard } from "@/components/recruitment/ai-analysis-card";
import { CandidateNotes } from "@/components/recruitment/candidate-notes";
import { InterviewScheduleForm } from "@/components/recruitment/interview-schedule-form";
import { ResumeUpload } from "@/components/recruitment/resume-upload";
import { Button } from "@/components/ui/button";
import {
  useAnalyzeCandidate,
  useApplicationTimeline,
  useCandidate,
  useCandidateAnalysis,
  useOverrideAI,
} from "@/hooks/use-candidates";
import { useInterviews } from "@/hooks/use-interviews";
import { useToast } from "@/hooks/use-toast";
import type { Interview } from "@/types/api";

export default function CandidateDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const toast = useToast();
  const applicationId = searchParams.get("applicationId") ?? undefined;
  const jobId = searchParams.get("jobId") ?? undefined;
  const [showSchedule, setShowSchedule] = useState(false);
  const [showOverride, setShowOverride] = useState(false);

  const candidateQuery = useCandidate(params.id);
  const analysisQuery = useCandidateAnalysis(params.id);
  const timelineQuery = useApplicationTimeline(applicationId);
  const interviewsQuery = useInterviews({ application_id: applicationId, page_size: 20 });
  const analyzeMutation = useAnalyzeCandidate();
  const overrideMutation = useOverrideAI();

  if (candidateQuery.isLoading) return <LoadingSpinner label="Loading candidate..." />;

  const candidate = candidateQuery.data;
  if (!candidate) return <p className="text-sm text-muted-foreground">Candidate not found.</p>;

  const interviewColumns: DataTableColumn<Interview>[] = [
    { key: "when", header: "Scheduled", render: (row) => new Date(row.scheduled_at).toLocaleString() },
    { key: "interviewer", header: "Interviewer", render: (row) => row.interviewer_name ?? "—" },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={candidate.full_name}
        description={`${candidate.email}${candidate.current_status ? ` · ${candidate.current_status}` : ""}`}
        action={
          applicationId ? (
            <Button type="button" onClick={() => setShowSchedule(true)}>
              Schedule interview
            </Button>
          ) : null
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="space-y-4 rounded-xl border bg-card p-4">
          <h2 className="text-base font-semibold">Resume upload</h2>
          <ResumeUpload
            candidateId={candidate.id}
            onUploaded={() => analysisQuery.refetch()}
            onAnalyze={async () => {
              if (!jobId) {
                toast.error("Missing job context for screening.");
                return;
              }
              await analyzeMutation.mutateAsync({ candidateId: candidate.id, jobId });
              toast.success("AI screening completed.");
              await analysisQuery.refetch();
            }}
          />
        </section>

        <section className="space-y-4">
          {analysisQuery.data ? (
            <AiAnalysisCard
              analysis={analysisQuery.data}
              onOverride={() => setShowOverride(true)}
            />
          ) : (
            <div className="rounded-xl border bg-card p-4 text-sm text-muted-foreground">
              No analysis available yet. Upload a resume and run AI screening.
            </div>
          )}
        </section>
      </div>

      <section className="rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-base font-semibold">Status timeline</h2>
        <ol className="space-y-3">
          {(timelineQuery.data ?? []).map((item, index) => (
            <li key={`${item.changed_at}-${index}`} className="border-l-2 border-primary pl-4">
              <p className="text-sm font-medium">
                {item.old_status ? `${item.old_status} → ` : ""}
                {item.new_status}
              </p>
              <p className="text-xs text-muted-foreground">
                {new Date(item.changed_at).toLocaleString()}
                {item.changed_by_name ? ` · ${item.changed_by_name}` : ""}
              </p>
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-base font-semibold">Notes</h2>
        <CandidateNotes candidateId={candidate.id} />
      </section>

      <section className="rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-base font-semibold">Interviews</h2>
        <DataTable
          columns={interviewColumns}
          rows={interviewsQuery.data?.items ?? []}
          isLoading={interviewsQuery.isLoading}
          getRowKey={(row) => row.id}
          emptyTitle="No interviews scheduled"
        />
      </section>

      {showSchedule && applicationId ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-xl border bg-background p-6">
            <h2 className="mb-4 text-lg font-semibold">Schedule interview</h2>
            <InterviewScheduleForm
              applicationId={applicationId}
              onCancel={() => setShowSchedule(false)}
              onSuccess={() => {
                setShowSchedule(false);
                void interviewsQuery.refetch();
              }}
            />
          </div>
        </div>
      ) : null}

      {showOverride && applicationId ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md space-y-4 rounded-xl border bg-background p-6">
            <h2 className="text-lg font-semibold">Override AI decision</h2>
            <div className="flex gap-2">
              <Button
                type="button"
                onClick={async () => {
                  await overrideMutation.mutateAsync({
                    applicationId,
                    status: "shortlisted",
                    remarks: "Manual override",
                  });
                  toast.success("Decision overridden.");
                  setShowOverride(false);
                }}
              >
                Shortlist
              </Button>
              <Button
                type="button"
                variant="destructive"
                onClick={async () => {
                  await overrideMutation.mutateAsync({
                    applicationId,
                    status: "rejected",
                    remarks: "Manual override",
                  });
                  toast.success("Decision overridden.");
                  setShowOverride(false);
                }}
              >
                Reject
              </Button>
              <Button type="button" variant="outline" onClick={() => setShowOverride(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
