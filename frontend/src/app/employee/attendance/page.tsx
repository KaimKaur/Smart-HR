"use client";

import { useState } from "react";

import { AttendanceCalendar } from "@/components/attendance/attendance-calendar";
import { CorrectionRequestDialog } from "@/components/attendance/correction-request-dialog";
import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { Button } from "@/components/ui/button";
import {
  useAttendanceHistory,
  useCheckIn,
  useCheckOut,
  useMonthlySummary,
  useMyEmployeeId,
  useRecordCorrections,
} from "@/hooks/use-attendance";
import { useToast } from "@/hooks/use-toast";
import type { AttendanceRecord } from "@/types/api";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function monthRange(year: number, month: number) {
  const start = `${year}-${String(month).padStart(2, "0")}-01`;
  const endDate = new Date(year, month, 0).getDate();
  const end = `${year}-${String(month).padStart(2, "0")}-${String(endDate).padStart(2, "0")}`;
  return { start, end };
}

export default function EmployeeAttendancePage() {
  const toast = useToast();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [page, setPage] = useState(1);
  const [correctionRecordId, setCorrectionRecordId] = useState<string | null>(null);

  const employeeIdQuery = useMyEmployeeId();
  const employeeId = employeeIdQuery.data ?? undefined;

  const today = todayIso();
  const { start, end } = monthRange(year, month);

  const todayHistory = useAttendanceHistory({
    date_from: today,
    date_to: today,
    page: 1,
    page_size: 1,
  });

  const historyQuery = useAttendanceHistory({
    date_from: start,
    date_to: end,
    page,
    page_size: 10,
  });

  const calendarHistory = useAttendanceHistory({
    date_from: start,
    date_to: end,
    page: 1,
    page_size: 100,
  });

  const monthlyQuery = useMonthlySummary(employeeId, year, month);
  const checkInMutation = useCheckIn();
  const checkOutMutation = useCheckOut();

  const todayRecord = todayHistory.data?.items[0];
  const hasCheckedIn = Boolean(todayRecord?.check_in_time);
  const hasCheckedOut = Boolean(todayRecord?.check_out_time);

  const correctionsQuery = useRecordCorrections(todayRecord?.id);
  const hasPendingCorrection = (correctionsQuery.data ?? []).some(
    (item) => item.correction_status === "pending",
  );

  const columns: DataTableColumn<AttendanceRecord>[] = [
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
    {
      key: "actions",
      header: "",
      render: (row) => (
        <Button type="button" size="sm" variant="outline" onClick={() => setCorrectionRecordId(row.id)}>
          Request correction
        </Button>
      ),
    },
  ];

  const summary = monthlyQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader title="My attendance" description="Check in, review your history, and request corrections." />

      <div className="rounded-xl border bg-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Today ({today})</p>
            <p className="text-sm">
              Check in: {todayRecord?.check_in_time ?? "—"} · Check out: {todayRecord?.check_out_time ?? "—"}
            </p>
            {hasPendingCorrection ? (
              <p className="mt-1 text-xs text-yellow-700">Pending correction request</p>
            ) : null}
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              disabled={!employeeId || hasCheckedIn || checkInMutation.isPending}
              onClick={async () => {
                await checkInMutation.mutateAsync(employeeId);
                toast.success("Checked in.");
                await todayHistory.refetch();
              }}
            >
              Check in
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={!employeeId || !hasCheckedIn || hasCheckedOut || checkOutMutation.isPending}
              onClick={async () => {
                await checkOutMutation.mutateAsync(employeeId);
                toast.success("Checked out.");
                await todayHistory.refetch();
              }}
            >
              Check out
            </Button>
          </div>
        </div>
      </div>

      {summary ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Present days" value={String(summary.present_days)} />
          <StatCard title="Absent days" value={String(summary.absent_days)} />
          <StatCard title="Late days" value={String(summary.late_days)} />
          <StatCard title="Total hours" value={summary.total_hours.toFixed(1)} />
        </div>
      ) : null}

      <section className="rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-base font-semibold">Calendar</h2>
        <AttendanceCalendar
          records={calendarHistory.data?.items ?? []}
          year={year}
          month={month}
          onMonthChange={(nextYear, nextMonth) => {
            setYear(nextYear);
            setMonth(nextMonth);
          }}
          onSelectRecord={(record) => setCorrectionRecordId(record.id)}
        />
      </section>

      <section className="space-y-4">
        <h2 className="text-base font-semibold">History</h2>
        <DataTable
          columns={columns}
          rows={historyQuery.data?.items ?? []}
          isLoading={historyQuery.isLoading}
          getRowKey={(row) => row.id}
          emptyTitle="No attendance records"
        />
        {historyQuery.data?.pagination ? (
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={page <= 1}
              onClick={() => setPage((value) => value - 1)}
            >
              Previous
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={page >= historyQuery.data.pagination.total_pages}
              onClick={() => setPage((value) => value + 1)}
            >
              Next
            </Button>
          </div>
        ) : null}
      </section>

      {correctionRecordId ? (
        <CorrectionRequestDialog
          recordId={correctionRecordId}
          onClose={() => setCorrectionRecordId(null)}
          onSuccess={() => void historyQuery.refetch()}
        />
      ) : null}
    </div>
  );
}
