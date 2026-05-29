"use client";

import { NotificationsBell } from "@/components/layout/notifications-bell";
import { UserProfileMenu } from "@/components/layout/user-profile-menu";
import { useAuth } from "@/hooks/useAuth";

export function TopBar() {
  const { user } = useAuth();

  return (
    <header className="flex h-14 items-center justify-between border-b bg-background px-4">
      <p className="text-sm text-muted-foreground">Welcome {user?.email ?? "User"}</p>
      <div className="flex items-center gap-2">
        <NotificationsBell />
        <UserProfileMenu />
      </div>
    </header>
  );
}
