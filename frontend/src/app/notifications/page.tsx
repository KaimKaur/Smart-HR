"use client";

import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { useMarkAllRead, useMarkRead, useNotifications } from "@/hooks/use-notifications";
import { useToast } from "@/hooks/use-toast";

type FilterValue = "all" | "unread" | "read";

export default function NotificationsPage() {
  const toast = useToast();
  const [filter, setFilter] = useState<FilterValue>("all");
  const [page, setPage] = useState(1);

  const notificationsQuery = useNotifications({
    is_read: filter === "all" ? undefined : filter === "read",
    page,
    page_size: 20,
  });
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();

  const rows = notificationsQuery.data?.items ?? [];
  const pagination = notificationsQuery.data?.pagination;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notifications"
        description="Review and manage your notifications."
        action={
          <Button
            type="button"
            variant="outline"
            disabled={markAllRead.isPending}
            onClick={async () => {
              await markAllRead.mutateAsync();
              toast.success("All notifications marked as read.");
              await notificationsQuery.refetch();
            }}
          >
            Mark all read
          </Button>
        }
      />

      <div className="flex gap-2">
        {(["all", "unread", "read"] as const).map((value) => (
          <Button
            key={value}
            type="button"
            variant={filter === value ? "default" : "outline"}
            onClick={() => {
              setFilter(value);
              setPage(1);
            }}
          >
            {value[0].toUpperCase() + value.slice(1)}
          </Button>
        ))}
      </div>

      <ul className="space-y-2">
        {rows.map((item) => (
          <li
            key={item.id}
            className={`rounded-lg border p-4 ${item.is_read ? "bg-background" : "bg-blue-50/60"}`}
          >
            <button
              type="button"
              className="w-full text-left"
              onClick={async () => {
                if (!item.is_read) {
                  await markRead.mutateAsync(item.id);
                  await notificationsQuery.refetch();
                }
              }}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-semibold">{item.title}</p>
                {!item.is_read ? <span className="mt-1 size-2 rounded-full bg-blue-600" /> : null}
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{item.message}</p>
              <p className="mt-2 text-xs text-muted-foreground">{new Date(item.created_at).toLocaleString()}</p>
            </button>
          </li>
        ))}
        {!notificationsQuery.isLoading && !rows.length ? (
          <li className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
            No notifications found.
          </li>
        ) : null}
      </ul>

      {pagination ? (
        <div className="flex items-center justify-between text-sm">
          <p className="text-muted-foreground">
            Page {pagination.page} of {pagination.total_pages} ({pagination.total_items} total)
          </p>
          <div className="flex gap-2">
            <Button type="button" variant="outline" disabled={page <= 1} onClick={() => setPage((v) => v - 1)}>
              Previous
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={page >= pagination.total_pages}
              onClick={() => setPage((v) => v + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

