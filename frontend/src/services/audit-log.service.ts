import { api } from "@/services/api";
import type { AuditLog, PaginatedResponse, SuccessResponse } from "@/types/api";

export interface AuditLogFilters {
  actor_user_id?: string;
  action?: string;
  resource_type?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export async function listAuditLogs(filters: AuditLogFilters = {}): Promise<PaginatedResponse<AuditLog>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<AuditLog>>>("/audit-logs", {
    params: filters,
  });
  return data.data;
}

