"use client";

import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { StatusBadge } from "@/components/common/status-badge";
import { useDailyAttendance } from "@/hooks/use-attendance";
import type { DailyAttendanceEmployee } from "@/types/api";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function HrDailyAttendancePage() {
  const [date, setDate] = useState(todayIso());
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const dailyQuery = useDailyAttendance(date);

  const filteredEmployees = useMemo(() => {
    const employees = dailyQuery.data?.employees ?? [];
    return employees.filter((employee) => {
      const matchesSearch =
        !search ||
        employee.full_name.toLowerCase().includes(search.toLowerCase()) ||
        employee.employee_code.toLowerCase().includes(search.toLowerCase());
      const matchesStatus =
        statusFilter === "all" ||
        employee.status_name.toLowerCase().includes(statusFilter.toLowerCase());
      return matchesSearch && matchesStatus;
    });
  }, [dailyQuery.data?.employees, search, statusFilter]);

  const columns: DataTableColumn<DailyAttendanceEmployee>[] = [
    { key: "name", header: "Employee", render: (row) => row.full_name },
    { key: "code", header: "Code", render: (row) => row.employee_code },
    { key: "department", header: "Department", render: (row) => row.department_name },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status_name} /> },
    { key: "in", header: "Check in", render: (row) => row.check_in_time ?? "—" },
    { key: "out", header: "Check out", render: (row) => row.check_out_time ?? "—" },
  ];

  const data = dailyQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader title="Daily attendance" description="Review attendance for all employees on a selected day." />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard title="Present" value={String(data?.present_count ?? 0)} />
        <StatCard title="Absent" value={String(data?.absent_count ?? 0)} />
        <StatCard title="Late" value={String(data?.late_count ?? 0)} />
      </div>

      <div className="grid gap-3 rounded-lg border bg-card p-4 sm:grid-cols-3">
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Date</span>
          <input
            type="date"
            className="h-9 rounded-lg border px-3"
            value={date}
            onChange={(event) => setDate(event.target.value)}
          />
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Search</span>
          <input
            className="h-9 rounded-lg border px-3"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Name or code"
          />
        </label>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Status</span>
          <select
            className="h-9 rounded-lg border px-3"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="all">All</option>
            <option value="present">Present</option>
            <option value="absent">Absent</option>
            <option value="late">Late</option>
          </select>
        </label>
      </div>

      <DataTable
        columns={columns}
        rows={filteredEmployees}
        isLoading={dailyQuery.isLoading}
        getRowKey={(row) => row.employee_id}
        emptyTitle="No employees found"
      />
    </div>
  );
}
