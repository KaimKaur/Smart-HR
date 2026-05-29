"use client";

import { useMemo, useState } from "react";

import { AttendanceCalendar } from "@/components/attendance/attendance-calendar";
import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { EmployeeSearch } from "@/components/employees/employee-search";
import { useAttendanceHistory, useMonthlySummary } from "@/hooks/use-attendance";
import type { AttendanceRecord } from "@/types/api";

function monthRange(year: number, month: number) {
  const endDate = new Date(year, month, 0).getDate();
  return {
    start: `${year}-${String(month).padStart(2, "0")}-01`,
    end: `${year}-${String(month).padStart(2, "0")}-${String(endDate).padStart(2, "0")}`,
  };
}

export default function HrMonthlyAttendancePage() {
  const now = new Date();
  const [employeeId, setEmployeeId] = useState<string | null>(null);
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const { start, end } = monthRange(year, month);
  const summaryQuery = useMonthlySummary(employeeId ?? undefined, year, month);
  const historyQuery = useAttendanceHistory({
    employee_id: employeeId ?? undefined,
    date_from: start,
    date_to: end,
    page: 1,
    page_size: 100,
  });

  const columns: DataTableColumn<AttendanceRecord>[] = useMemo(
    () => [
      { key: "date", header: "Date", render: (row) => row.attendance_date },
      { key: "status", header: "Status", render: (row) => row.status_name },
      { key: "in", header: "Check in", render: (row) => row.check_in_time ?? "—" },
      { key: "out", header: "Check out", render: (row) => row.check_out_time ?? "—" },
      {
        key: "hours",
        header: "Hours",
        render: (row) =>
          row.work_duration_minutes ? (row.work_duration_minutes / 60).toFixed(1) : "—",
      },
    ],
    [],
  );

  const summary = summaryQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Monthly attendance summary"
        description="Select an employee and month to review attendance breakdown."
      />

      <div className="grid gap-3 rounded-lg border bg-card p-4 sm:grid-cols-3">
        <label className="grid gap-1 text-sm sm:col-span-1">
          <span className="font-medium">Employee</span>
          <EmployeeSearch value={employeeId} onChange={(id) => setEmployeeId(id)} />
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Year</span>
          <input
            type="number"
            className="h-9 rounded-lg border px-3"
            value={year}
            onChange={(event) => setYear(Number(event.target.value))}
          />
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Month</span>
          <input
            type="number"
            min={1}
            max={12}
            className="h-9 rounded-lg border px-3"
            value={month}
            onChange={(event) => setMonth(Number(event.target.value))}
          />
        </label>
      </div>

      {!employeeId ? (
        <p className="text-sm text-muted-foreground">Select an employee to view monthly summary.</p>
      ) : (
        <>
          {summary ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard title="Present" value={String(summary.present_days)} />
              <StatCard title="Absent" value={String(summary.absent_days)} />
              <StatCard title="Late" value={String(summary.late_days)} />
              <StatCard title="Total hours" value={summary.total_hours.toFixed(1)} />
            </div>
          ) : null}

          <section className="rounded-xl border bg-card p-4">
            <h2 className="mb-4 text-base font-semibold">Calendar</h2>
            <AttendanceCalendar
              records={historyQuery.data?.items ?? []}
              year={year}
              month={month}
              onMonthChange={(nextYear, nextMonth) => {
                setYear(nextYear);
                setMonth(nextMonth);
              }}
            />
          </section>

          <section className="space-y-4">
            <h2 className="text-base font-semibold">Daily breakdown</h2>
            <DataTable
              columns={columns}
              rows={historyQuery.data?.items ?? []}
              isLoading={historyQuery.isLoading}
              getRowKey={(row) => row.id}
              emptyTitle="No records for this month"
            />
          </section>
        </>
      )}
    </div>
  );
}
