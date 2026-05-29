'use client'

"use client";

import Link from "next/link";
import { useMemo } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { useRecruitmentDashboard } from "@/hooks/use-dashboard";
import type { RecruitmentJobSummary } from "@/types/api";

const COLORS = ["#2563eb", "#16a34a", "#dc2626", "#f59e0b"];

export default function RecruiterDashboardPage() {
  const dashboardQuery = useRecruitmentDashboard();
  const data = dashboardQuery.data;

  const donutData = useMemo(() => {
    if (!data) return [];
    return [
      { name: "Shortlisted", value: data.shortlisted_candidates },
      { name: "Pending screening", value: data.pending_screening_candidates },
      { name: "Rejected", value: data.rejected_candidates },
      {
        name: "Other",
        value: Math.max(0, data.total_candidates - data.shortlisted_candidates - data.pending_screening_candidates - data.rejected_candidates),
      },
    ];
  }, [data]);

  const columns: DataTableColumn<RecruitmentJobSummary>[] = [
    {
      key: "job",
      header: "Job",
      render: (row) => (
        <Link className="text-primary hover:underline" href={`/recruiter/jobs/${row.job_id}`}>
          {row.title}
        </Link>
      ),
    },
    { key: "open", header: "Open", render: (row) => row.open_applications },
    { key: "shortlisted", header: "Shortlisted", render: (row) => row.shortlisted_applications },
    { key: "rejected", header: "Rejected", render: (row) => row.rejected_applications },
    {
      key: "avg",
      header: "Avg AI score",
      render: (row) => (row.average_ai_score != null ? row.average_ai_score.toFixed(1) : "—"),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Recruitment dashboard" description="Recruitment KPIs and top jobs." />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Open jobs" value={data?.open_jobs} isLoading={dashboardQuery.isLoading} />
        <StatCard title="Total candidates" value={data?.total_candidates} isLoading={dashboardQuery.isLoading} />
        <StatCard
          title="Shortlisted %"
          value={
            data?.total_candidates
              ? `${((data.shortlisted_candidates / data.total_candidates) * 100).toFixed(1)}%`
              : "—"
          }
          isLoading={dashboardQuery.isLoading}
        />
        <StatCard
          title="Average AI score"
          value={data?.average_ai_score != null ? data.average_ai_score.toFixed(1) : "—"}
          isLoading={dashboardQuery.isLoading}
        />
      </div>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-4 text-base font-semibold">Candidate status distribution</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={donutData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90}>
                  {donutData.map((_, idx) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-3 rounded-xl border bg-card p-4">
          <h2 className="text-base font-semibold">Top candidates per job</h2>
          <p className="text-sm text-muted-foreground">
            Open a job to view the full candidate list and ranking details.
          </p>
          <DataTable
            columns={columns}
            rows={data?.jobs ?? []}
            isLoading={dashboardQuery.isLoading}
            getRowKey={(row) => row.job_id}
            emptyTitle="No jobs found"
          />
        </div>
      </section>
    </div>
  );
}

