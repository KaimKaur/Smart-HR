"use client";

import Link from "next/link";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import type { RoleSlug } from "@/types/api";

function formatRole(role: RoleSlug): string {
  return role
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function UserProfileMenu() {
  const { user, logout } = useAuth();

  const primaryRole = useMemo(() => {
    const role = user?.roles?.[0];
    return role ? formatRole(role) : "User";
  }, [user]);

  const label = user?.email ?? "Account";

  return (
    <details className="relative">
      <summary className="list-none">
        <Button type="button" variant="outline" aria-label="Open user menu">
          {label}
        </Button>
      </summary>
      <div
        className="absolute right-0 z-50 mt-2 w-64 rounded-lg border bg-popover p-2 text-sm shadow-md"
        role="menu"
        aria-label="User menu"
      >
        <div className="px-2 py-2">
          <p className="truncate font-medium">{user?.email ?? "Signed out"}</p>
          <p className="truncate text-xs text-muted-foreground">{primaryRole}</p>
        </div>
        <div className="my-2 h-px bg-border" />
        <Link
          className="block rounded-md px-2 py-2 hover:bg-muted"
          href="/profile"
          role="menuitem"
        >
          Profile
        </Link>
        <button
          type="button"
          className="w-full rounded-md px-2 py-2 text-left hover:bg-muted"
          role="menuitem"
          onClick={() => void logout()}
        >
          Logout
        </button>
      </div>
    </details>
  );
}

