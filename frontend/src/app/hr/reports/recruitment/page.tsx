"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { Button } from "@/components/ui/button";
import { useApiQuery } from "@/hooks/use-api-query";
import { useToast } from "@/hooks/use-toast";
import { downloadBlob } from "@/lib/download";
import { listJobs } from "@/services/job.service";
import { exportRecruitmentReport, getRecruitmentReport } from "@/services/reporting.service";
import type { RecruitmentReportRow } from "@/types/api";

export default function RecruitmentReportPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [isExporting, setIsExporting] = useState(false);

  const filters = useMemo(
    () => ({
      job_id: searchParams.get("job_id") || undefined,
      status: searchParams.get("status") || undefined,
      date_from: searchParams.get("date_from") || undefined,
      date_to: searchParams.get("date_to") || undefined,
      page: Number(searchParams.get("page") || "1"),
      page_size: 20,
    }),
    [searchParams],
  );

  const reportQuery = useApiQuery({
    queryKey: ["recruitment-report", filters],
    queryFn: () => getRecruitmentReport(filters),
  });

  const jobsQuery = useApiQuery({
    queryKey: ["jobs", "report-filter"],
    queryFn: () => listJobs({ page: 1, page_size: 100 }),
  });

  const rows = reportQuery.data?.items ?? [];
  const totals = rows.reduce(
    (acc, row) => ({
      candidates: acc.candidates + row.total_candidates,
      shortlisted: acc.shortlisted + row.shortlisted,
      scores: acc.scores + (row.average_ai_score ?? 0),
      count: acc.count + 1,
    }),
    { candidates: 0, shortlisted: 0, scores: 0, count: 0 },
  );

  const shortlistedPct =
    totals.candidates > 0 ? Math.round((totals.shortlisted / totals.candidates) * 100) : 0;
  const averageScore = totals.count > 0 ? (totals.scores / totals.count).toFixed(1) : "—";

  const updateParams = (updates: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([key, value]) => {
      if (!value) params.delete(key);
      else params.set(key, value);
    });
    router.replace(`/hr/reports/recruitment?${params.toString()}`);
  };

  const columns: DataTableColumn<RecruitmentReportRow>[] = [
    { key: "job", header: "Job", render: (row) => row.job_title },
    { key: "total", header: "Candidates", render: (row) => row.total_candidates },
    { key: "shortlisted", header: "Shortlisted", render: (row) => row.shortlisted },
    { key: "rejected", header: "Rejected", render: (row) => row.rejected },
    { key: "pending", header: "Pending", render: (row) => row.pending },
    { key: "avg", header: "Avg AI score", render: (row) => row.average_ai_score ?? "—" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recruitment report"
        description="Pipeline metrics and exportable candidate statistics."
        action={
          <Button
            type="button"
            disabled={isExporting}
            onClick={async () => {
              setIsExporting(true);
              try {
                const blob = await exportRecruitmentReport({
                  job_id: filters.job_id,
                  status: filters.status,
                  date_from: filters.date_from,
                  date_to: filters.date_to,
                });
                downloadBlob(blob, "recruitment_report.csv");
                toast.success("CSV export downloaded.");
              } catch {
                toast.error("Unable to export report.");
              } finally {
                setIsExporting(false);
              }
            }}
          >
            {isExporting ? "Exporting..." : "Export CSV"}
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard title="Total candidates" value={String(totals.candidates)} />
        <StatCard title="Shortlisted %" value={`${shortlistedPct}%`} />
        <StatCard title="Average score" value={String(averageScore)} />
      </div>

      <div className="grid gap-3 rounded-lg border bg-card p-4 sm:grid-cols-2 lg:grid-cols-4">
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Job</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={filters.job_id ?? ""}
            onChange={(event) => updateParams({ job_id: event.target.value || null, page: "1" })}
          >
            <option value="">All jobs</option>
            {(jobsQuery.data?.items ?? []).map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Status</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={filters.status ?? ""}
            onChange={(event) => updateParams({ status: event.target.value || null, page: "1" })}
          >
            <option value="">All</option>
            <option value="applied">Applied</option>
            <option value="shortlisted">Shortlisted</option>
            <option value="rejected">Rejected</option>
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">From</span>
          <input
            type="date"
            className="h-9 rounded-lg border px-3"
            value={filters.date_from ?? ""}
            onChange={(event) => updateParams({ date_from: event.target.value || null, page: "1" })}
          />
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">To</span>
          <input
            type="date"
            className="h-9 rounded-lg border px-3"
            value={filters.date_to ?? ""}
            onChange={(event) => updateParams({ date_to: event.target.value || null, page: "1" })}
          />
        </label>
      </div>

      <DataTable
        columns={columns}
        rows={rows}
        isLoading={reportQuery.isLoading}
        getRowKey={(row) => row.job_id}
        emptyTitle="No recruitment data"
      />
    </div>
  );
}
