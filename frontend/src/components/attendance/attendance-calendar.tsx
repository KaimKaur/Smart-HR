"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import type { AttendanceRecord } from "@/types/api";
import { cn } from "@/lib/utils";

function statusColor(status: string): string {
  const normalized = status.toLowerCase();
  if (normalized.includes("present")) return "bg-green-500";
  if (normalized.includes("absent")) return "bg-red-500";
  if (normalized.includes("late")) return "bg-yellow-500";
  if (normalized.includes("holiday") || normalized.includes("weekend")) return "bg-gray-400";
  return "bg-blue-400";
}

export function AttendanceCalendar({
  records,
  year,
  month,
  onMonthChange,
  onSelectRecord,
}: {
  records: AttendanceRecord[];
  year: number;
  month: number;
  onMonthChange: (year: number, month: number) => void;
  onSelectRecord?: (record: AttendanceRecord) => void;
}) {
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const recordsByDate = useMemo(() => {
    const map = new Map<string, AttendanceRecord>();
    records.forEach((record) => map.set(record.attendance_date, record));
    return map;
  }, [records]);

  const firstDay = new Date(year, month - 1, 1);
  const daysInMonth = new Date(year, month, 0).getDate();
  const startWeekday = firstDay.getDay();

  const days: Array<number | null> = [
    ...Array.from({ length: startWeekday }, () => null),
    ...Array.from({ length: daysInMonth }, (_, index) => index + 1),
  ];

  const selectedRecord = selectedDate ? recordsByDate.get(selectedDate) : undefined;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            const prev = new Date(year, month - 2, 1);
            onMonthChange(prev.getFullYear(), prev.getMonth() + 1);
          }}
        >
          Previous
        </Button>
        <p className="font-medium">
          {firstDay.toLocaleString("default", { month: "long" })} {year}
        </p>
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            const next = new Date(year, month, 1);
            onMonthChange(next.getFullYear(), next.getMonth() + 1);
          }}
        >
          Next
        </Button>
      </div>

      <div className="grid grid-cols-7 gap-2 text-center text-xs font-medium text-muted-foreground">
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
          <div key={day}>{day}</div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-2">
        {days.map((day, index) => {
          if (!day) return <div key={`empty-${index}`} />;
          const isoDate = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const record = recordsByDate.get(isoDate);
          return (
            <button
              key={isoDate}
              type="button"
              className={cn(
                "flex h-12 flex-col items-center justify-center rounded-lg border text-xs",
                selectedDate === isoDate && "ring-2 ring-primary",
              )}
              onClick={() => {
                setSelectedDate(isoDate);
                if (record) onSelectRecord?.(record);
              }}
            >
              <span>{day}</span>
              <span
                className={cn(
                  "mt-1 h-2 w-2 rounded-full",
                  record ? statusColor(record.status_name) : "bg-transparent",
                )}
              />
            </button>
          );
        })}
      </div>

      {selectedRecord ? (
        <div className="rounded-lg border bg-card p-4 text-sm">
          <p className="font-medium">{selectedRecord.attendance_date}</p>
          <p>Status: {selectedRecord.status_name}</p>
          <p>Check in: {selectedRecord.check_in_time ?? "—"}</p>
          <p>Check out: {selectedRecord.check_out_time ?? "—"}</p>
        </div>
      ) : selectedDate ? (
        <p className="text-sm text-muted-foreground">No attendance record for {selectedDate}.</p>
      ) : null}
    </div>
  );
}
