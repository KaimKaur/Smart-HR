"use client";

import type { RoleSlug } from "@/types/api";
import { useAuthContext } from "@/providers/auth-provider";

export function useAuth() {
  const ctx = useAuthContext();

  return {
    user: ctx.user,
    isAuthenticated: ctx.isAuthenticated,
    isLoading: ctx.isLoading,
    login: ctx.login,
    refreshToken: ctx.refreshToken,
    logout: ctx.logout,
    hasRole: (role: RoleSlug) => ctx.hasRole(role),
  };
}

