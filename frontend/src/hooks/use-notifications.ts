"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation, useApiQuery } from "@/hooks/use-api-query";
import {
  getNotificationPreferences,
  getUnreadNotificationCount,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  updateNotificationPreferences,
  type NotificationPreference,
} from "@/services/notification.service";

export const notificationKeys = {
  all: ["notifications"] as const,
  list: (params?: { is_read?: boolean; page?: number; page_size?: number }) =>
    [...notificationKeys.all, "list", params] as const,
  unread: () => [...notificationKeys.all, "unread"] as const,
  preferences: () => [...notificationKeys.all, "preferences"] as const,
};

export function useNotifications(params?: { is_read?: boolean; page?: number; page_size?: number }) {
  return useApiQuery({
    queryKey: notificationKeys.list(params),
    queryFn: () => listNotifications(params),
  });
}

export function useUnreadCount(enabled = true) {
  return useApiQuery({
    queryKey: notificationKeys.unread(),
    queryFn: getUnreadNotificationCount,
    enabled,
    refetchInterval: 30_000,
    notifyOnChangeProps: ["data", "error"],
  });
}

export function useMarkRead() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (notificationId: string) => markNotificationRead(notificationId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: notificationKeys.list() });
      await queryClient.invalidateQueries({ queryKey: notificationKeys.unread() });
    },
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useApiMutation<void, void>({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: notificationKeys.list() });
      await queryClient.invalidateQueries({ queryKey: notificationKeys.unread() });
    },
  });
}

export function useNotificationPreferences() {
  return useApiQuery({
    queryKey: notificationKeys.preferences(),
    queryFn: getNotificationPreferences,
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useApiMutation({
    mutationFn: (payload: NotificationPreference) => updateNotificationPreferences(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: notificationKeys.preferences() });
    },
  });
}

// Backward-compatible aliases for existing imports.
export const useUnreadNotificationCount = useUnreadCount;
export const useMarkNotificationRead = useMarkRead;
