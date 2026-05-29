"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { clearTokens, getRefreshToken, setRoleCookie, setTokens } from "@/lib/auth-storage";
import {
  getMe,
  login as loginRequest,
  logout as logoutRequest,
  refreshToken as refreshTokenRequest,
} from "@/services/auth.service";
import type { RoleSlug, User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  refreshToken: () => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: RoleSlug) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const restoreSession = useCallback(async () => {
    try {
      const refreshToken = getRefreshToken();
      if (!refreshToken) return;
      const me = await getMe();
      setUser(me);
      setRoleCookie(me.roles);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await loginRequest({ email, password });
    setTokens(tokens.access_token, tokens.refresh_token);
    const me = await getMe();
    setUser(me);
    setRoleCookie(me.roles);
    return me;
  }, []);

  const refreshToken = useCallback(async () => {
    const refresh = getRefreshToken();
    if (!refresh) throw new Error("Missing refresh token");
    const tokens = await refreshTokenRequest(refresh);
    setTokens(tokens.access_token, tokens.refresh_token);
    const me = await getMe();
    setUser(me);
    setRoleCookie(me.roles);
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      clearTokens();
      setUser(null);
      if (typeof window !== "undefined") window.location.href = "/login";
    }
  }, []);

  const hasRole = useCallback(
    (role: RoleSlug) => {
      if (!user) return false;
      return user.roles.includes(role);
    },
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      login,
      refreshToken,
      logout,
      hasRole,
    }),
    [user, isLoading, login, refreshToken, logout, hasRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return context;
}
