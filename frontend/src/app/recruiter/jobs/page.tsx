"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { JobForm } from "@/components/recruitment/job-form";
import { Button } from "@/components/ui/button";
import { useCloseJob, useCreateJob, useJobs, usePublishJob } from "@/hooks/use-jobs";
import { useToast } from "@/hooks/use-toast";
import { getApplicationCount } from "@/services/job.service";
import type { Job } from "@/types/api";

const STATUS_TABS = ["all", "draft", "published", "closed"] as const;

export default function JobListPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [counts, setCounts] = useState<Record<string, number>>({});

  const statusFilter = searchParams.get("status") ?? "all";
  const filters = useMemo(
    () => ({
      status: statusFilter === "all" ? undefined : statusFilter,
      page: Number(searchParams.get("page") || "1"),
      page_size: 20,
    }),
    [searchParams, statusFilter],
  );

  const jobsQuery = useJobs(filters);
  const createMutation = useCreateJob();
  const publishMutation = usePublishJob();
  const closeMutation = useCloseJob();

  useEffect(() => {
    const jobs = jobsQuery.data?.items ?? [];
    void Promise.all(
      jobs.map(async (job) => {
        const count = await getApplicationCount(job.id);
        return [job.id, count] as const;
      }),
    ).then((entries) => setCounts(Object.fromEntries(entries)));
  }, [jobsQuery.data?.items]);

  const setStatusTab = (status: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (status === "all") params.delete("status");
    else params.set("status", status);
    params.set("page", "1");
    router.replace(`/recruiter/jobs?${params.toString()}`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Jobs"
        description="Manage open roles and hiring pipelines."
        action={
          <Button type="button" onClick={() => setShowCreate(true)}>
            Create Job
          </Button>
        }
      />

      <div className="flex flex-wrap gap-2">
        {STATUS_TABS.map((tab) => (
          <Button
            key={tab}
            type="button"
            variant={statusFilter === tab ? "default" : "outline"}
            onClick={() => setStatusTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </Button>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(jobsQuery.data?.items ?? []).map((job) => (
          <JobCard
            key={job.id}
            job={job}
            candidateCount={counts[job.id]}
            onPublish={async () => {
              await publishMutation.mutateAsync(job.id);
              toast.success("Job published.");
            }}
            onClose={async () => {
              await closeMutation.mutateAsync(job.id);
              toast.success("Job closed.");
            }}
          />
        ))}
      </div>

      {showCreate ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border bg-background p-6">
            <h2 className="mb-4 text-lg font-semibold">Create job</h2>
            <JobForm
              mode="create"
              isSubmitting={createMutation.isPending}
              onCancel={() => setShowCreate(false)}
              onSubmit={async (values) => {
                await createMutation.mutateAsync(values);
                toast.success("Job created.");
                setShowCreate(false);
              }}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function JobCard({
  job,
  candidateCount,
  onPublish,
  onClose,
}: {
  job: Job;
  candidateCount?: number;
  onPublish: () => Promise<void>;
  onClose: () => Promise<void>;
}) {
  return (
    <article className="rounded-xl border bg-card p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <Link href={`/recruiter/jobs/${job.id}`} className="text-lg font-semibold hover:underline">
            {job.title}
          </Link>
          <p className="mt-1 text-sm text-muted-foreground">{job.department_name ?? "No department"}</p>
        </div>
        <StatusBadge status={job.status} />
      </div>
      <div className="mt-4 space-y-1 text-sm text-muted-foreground">
        <p>Candidates: {candidateCount ?? "—"}</p>
        <p>Created: {new Date(job.created_at).toLocaleDateString()}</p>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button asChild size="sm" variant="outline">
          <Link href={`/recruiter/jobs/${job.id}`}>View</Link>
        </Button>
        {job.status === "draft" ? (
          <Button size="sm" type="button" onClick={() => void onPublish()}>
            Publish
          </Button>
        ) : null}
        {job.status === "published" ? (
          <Button size="sm" type="button" variant="outline" onClick={() => void onClose()}>
            Close
          </Button>
        ) : null}
      </div>
    </article>
  );
}
