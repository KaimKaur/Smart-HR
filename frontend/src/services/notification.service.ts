import { api } from "@/services/api";
import type { Notification, PaginatedResponse, SuccessResponse } from "@/types/api";

export interface NotificationPreference {
  in_app_enabled: boolean;
}

export async function listNotifications(params?: {
  is_read?: boolean;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Notification>> {
  const { data } = await api.get<SuccessResponse<PaginatedResponse<Notification>>>("/notifications", {
    params,
  });
  return data.data;
}

export async function getUnreadNotificationCount(): Promise<number> {
  const { data } = await api.get<SuccessResponse<{ unread_count: number }>>("/notifications/unread-count");
  return data.data.unread_count;
}

export async function markNotificationRead(notificationId: string): Promise<void> {
  await api.patch(`/notifications/${notificationId}/read`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await api.post("/notifications/read-all");
}

export async function getNotificationPreferences(): Promise<NotificationPreference> {
  const { data } = await api.get<SuccessResponse<NotificationPreference>>("/notifications/preferences");
  return data.data;
}

export async function updateNotificationPreferences(
  payload: NotificationPreference,
): Promise<NotificationPreference> {
  const { data } = await api.patch<SuccessResponse<NotificationPreference>>(
    "/notifications/preferences",
    payload,
  );
  return data.data;
}
