import { api } from "@/services/api";
import type {
  AttendanceCorrection,
  AttendanceRecord,
  AttendanceReportRow,
  DailyAttendance,
  MonthlyAttendanceSummary,
  PaginatedResponse,
  SuccessResponse,
} from "@/types/api";

export interface AttendanceListFilters {
  employee_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface AttendanceModuleReportFilters {
  date_from: string;
  date_to: string;
  department_id?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export async function checkIn(employeeId?: string): Promise<AttendanceRecord> {
  const { data } = await api.post<SuccessResponse<AttendanceRecord>>(
    "/attendance/check-in",
    {},
    { params: employeeId ? { employee_id: employeeId } : undefined },
  );
  return data.data;
}

export async function checkOut(employeeId?: string): Promise<AttendanceRecord> {
  const { data } = await api.post<SuccessResponse<AttendanceRecord>>(
    "/attendance/check-out",
    {},
    { params: employeeId ? { employee_id: employeeId } : undefined },
  );
  return data.data;
}

export async function listAttendance(
  filters: AttendanceListFilters = {},
): Promise<PaginatedResponse<AttendanceRecord>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<AttendanceRecord>>>(
    "/attendance",
    { params: filters },
  );
  return data.data;
}

export async function getMonthlySummary(
  employeeId: string,
  year: number,
  month: number,
): Promise<MonthlyAttendanceSummary> {
  const { data } = await api.get<SuccessResponse<MonthlyAttendanceSummary>>(
    "/attendance/monthly",
    { params: { employee_id: employeeId, year, month } },
  );
  return data.data;
}

export async function getDailyAttendance(date: string): Promise<DailyAttendance> {
  const { data } = await api.get<SuccessResponse<DailyAttendance>>("/attendance/daily", {
    params: { date },
  });
  return data.data;
}

export async function getAttendanceModuleReport(
  filters: AttendanceModuleReportFilters,
): Promise<PaginatedResponse<AttendanceReportRow>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<AttendanceReportRow>>>(
    "/attendance/report",
    { params: filters },
  );
  return data.data;
}

export async function requestCorrection(
  recordId: string,
  reason: string,
): Promise<AttendanceCorrection> {
  const { data } = await api.post<SuccessResponse<AttendanceCorrection>>(
    `/attendance/${recordId}/corrections`,
    { reason },
  );
  return data.data;
}

export async function listCorrections(recordId: string): Promise<AttendanceCorrection[]> {
  const { data } = await api.get<SuccessResponse<{ items: AttendanceCorrection[] }>>(
    `/attendance/${recordId}/corrections`,
  );
  return data.data.items;
}

export async function reviewCorrection(
  correctionId: string,
  status: "approved" | "rejected",
): Promise<AttendanceCorrection> {
  const { data } = await api.patch<SuccessResponse<AttendanceCorrection>>(
    `/attendance/corrections/${correctionId}`,
    { status },
  );
  return data.data;
}

export async function listPendingCorrections(
  dateFrom: string,
  dateTo: string,
): Promise<Array<AttendanceCorrection & { record?: AttendanceReportRow }>> {
  const report = await getAttendanceModuleReport({
    date_from: dateFrom,
    date_to: dateTo,
    page: 1,
    page_size: 100,
  });

  const pending: Array<AttendanceCorrection & { record?: AttendanceReportRow }> = [];
  await Promise.all(
    report.items.map(async (row) => {
      const corrections = await listCorrections(row.record_id);
      corrections
        .filter((item) => item.correction_status === "pending")
        .forEach((item) => pending.push({ ...item, record: row }));
    }),
  );
  return pending.sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
}
