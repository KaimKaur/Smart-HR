"use client";

import Link from "next/link";
import { Bell } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useMarkRead, useNotifications, useUnreadCount } from "@/hooks/use-notifications";

function timeAgo(iso: string): string {
  const deltaMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(deltaMs / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function NotificationsBell() {
  const { isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const unreadCountQuery = useUnreadCount(isAuthenticated);
  const notificationsQuery = useNotifications({
    page: 1,
    page_size: 5,
  });
  const markRead = useMarkRead();

  const unreadCount = unreadCountQuery.data ?? 0;
  const items = useMemo(() => notificationsQuery.data?.items ?? [], [notificationsQuery.data?.items]);

  useEffect(() => {
    if (!isOpen) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    window.addEventListener("mousedown", onPointerDown);
    return () => window.removeEventListener("mousedown", onPointerDown);
  }, [isOpen]);

  return (
    <div className="relative" ref={containerRef}>
      <Button
        type="button"
        variant="ghost"
        size="icon-sm"
        aria-label="Notifications"
        onClick={() => setIsOpen((value) => !value)}
      >
        <Bell />
        {unreadCount > 0 ? (
          <span className="absolute -right-1 -top-1 rounded-full bg-red-600 px-1.5 text-[10px] text-white">
            {unreadCount}
          </span>
        ) : null}
      </Button>

      {isOpen ? (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-lg border bg-popover p-2 shadow-md">
          <div className="mb-2 flex items-center justify-between px-1">
            <p className="text-sm font-semibold">Notifications</p>
            <Link href="/notifications" className="text-xs text-primary hover:underline" onClick={() => setIsOpen(false)}>
              View all
            </Link>
          </div>

          <ul className="space-y-1">
            {items.map((item) => (
              <li key={item.id}>
                <Link
                  href="/notifications"
                  className="block rounded-md border px-2 py-2 hover:bg-muted"
                  onClick={async () => {
                    if (!item.is_read) {
                      await markRead.mutateAsync(item.id);
                    }
                    setIsOpen(false);
                  }}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium">{item.title}</p>
                    {!item.is_read ? <span className="mt-1 size-2 rounded-full bg-blue-600" /> : null}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{item.message}</p>
                  <p className="mt-1 text-[11px] text-muted-foreground">{timeAgo(item.created_at)}</p>
                </Link>
              </li>
            ))}
            {!notificationsQuery.isLoading && !items.length ? (
              <li className="rounded-md border border-dashed px-2 py-3 text-xs text-muted-foreground">
                No notifications.
              </li>
            ) : null}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

