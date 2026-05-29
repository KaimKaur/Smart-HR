"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { JobForm } from "@/components/recruitment/job-form";
import { Button } from "@/components/ui/button";
import { useCloseJob, useJob, usePublishJob, useUpdateJob } from "@/hooks/use-jobs";
import { useToast } from "@/hooks/use-toast";
import { getApplicationCount } from "@/services/job.service";
import { useApiQuery } from "@/hooks/use-api-query";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const toast = useToast();
  const tab = searchParams.get("tab") ?? "overview";
  const [showEdit, setShowEdit] = useState(false);

  const jobQuery = useJob(params.id);
  const updateMutation = useUpdateJob(params.id);
  const publishMutation = usePublishJob();
  const closeMutation = useCloseJob();

  const countQuery = useApiQuery({
    queryKey: ["job-count", params.id],
    queryFn: () => getApplicationCount(params.id),
    enabled: Boolean(params.id),
  });

  const job = jobQuery.data;
  if (!job) return <p className="text-sm text-muted-foreground">Loading job...</p>;

  return (
    <div className="space-y-6">
      <PageHeader
        title={job.title}
        description={job.department_name ?? "No department assigned"}
        action={
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => setShowEdit(true)}>
              Edit
            </Button>
            {job.status === "draft" ? (
              <Button
                type="button"
                onClick={async () => {
                  await publishMutation.mutateAsync(job.id);
                  toast.success("Job published.");
                }}
              >
                Publish
              </Button>
            ) : null}
            {job.status === "published" ? (
              <Button
                type="button"
                variant="outline"
                onClick={async () => {
                  await closeMutation.mutateAsync(job.id);
                  toast.success("Job closed.");
                }}
              >
                Close
              </Button>
            ) : null}
          </div>
        }
      />

      <div className="flex flex-wrap gap-2">
        <Button asChild variant={tab === "overview" ? "default" : "outline"}>
          <Link href={`/recruiter/jobs/${job.id}`}>Overview</Link>
        </Button>
        <Button asChild variant={tab === "candidates" ? "default" : "outline"}>
          <Link href={`/recruiter/jobs/${job.id}/candidates`}>Candidates</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href={`/recruiter/jobs/${job.id}/ranking`}>Ranking</Link>
        </Button>
      </div>

      <div className="rounded-xl border bg-card p-4 space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Status:</span>
          <StatusBadge status={job.status} />
        </div>
        <p className="text-sm whitespace-pre-wrap">{job.description}</p>
        <div>
          <p className="mb-2 text-sm font-medium">Skills</p>
          <div className="flex flex-wrap gap-2">
            {job.skills.map((skill) => (
              <span key={skill} className="rounded-full bg-muted px-2 py-1 text-xs">
                {skill}
              </span>
            ))}
          </div>
        </div>
        <p className="text-sm text-muted-foreground">
          Candidates: {countQuery.data ?? "—"} · Updated {new Date(job.updated_at).toLocaleDateString()}
        </p>
        <Button asChild>
          <Link href={`/recruiter/jobs/${job.id}/candidates`}>View candidates</Link>
        </Button>
      </div>

      {showEdit ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border bg-background p-6">
            <h2 className="mb-4 text-lg font-semibold">Edit job</h2>
            <JobForm
              mode="edit"
              initial={job}
              isSubmitting={updateMutation.isPending}
              onCancel={() => setShowEdit(false)}
              onSubmit={async (values) => {
                await updateMutation.mutateAsync(values);
                toast.success("Job updated.");
                setShowEdit(false);
              }}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
