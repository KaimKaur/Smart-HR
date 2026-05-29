import { api } from "@/services/api";
import type { PaginatedResponse, SuccessResponse } from "@/types/api";

export interface AdminUser {
  id: string;
  email: string;
  is_active: boolean;
  roles: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateAdminUserPayload {
  email: string;
  roles: string[];
  is_active?: boolean;
}

export interface UpdateAdminUserPayload {
  email?: string;
  is_active?: boolean;
}

export async function listUsers(params?: {
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<AdminUser>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<AdminUser>>>("/users", {
    params,
  });
  return data.data;
}

export async function createUser(payload: CreateAdminUserPayload): Promise<AdminUser> {
  const { data } = await api.post<SuccessResponse<AdminUser>>("/users", payload);
  return data.data;
}

export async function updateUser(userId: string, payload: UpdateAdminUserPayload): Promise<AdminUser> {
  const { data } = await api.patch<SuccessResponse<AdminUser>>(`/users/${userId}`, payload);
  return data.data;
}

export async function deactivateUser(userId: string): Promise<void> {
  await api.delete(`/users/${userId}`);
}

export async function assignRole(userId: string, role: string): Promise<AdminUser> {
  const { data } = await api.post<SuccessResponse<AdminUser>>(`/users/${userId}/roles`, { role });
  return data.data;
}

export async function removeRole(userId: string, roleId: string): Promise<AdminUser> {
  const { data } = await api.delete<SuccessResponse<AdminUser>>(`/users/${userId}/roles/${roleId}`);
  return data.data;
}

