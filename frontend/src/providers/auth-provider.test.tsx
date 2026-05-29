import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuthContext } from "@/providers/auth-provider";

const getRefreshTokenMock = vi.fn();
const setTokensMock = vi.fn();
const setRoleCookieMock = vi.fn();
const clearTokensMock = vi.fn();
const getMeMock = vi.fn();
const loginRequestMock = vi.fn();
const refreshTokenRequestMock = vi.fn();
const logoutRequestMock = vi.fn();

vi.mock("@/lib/auth-storage", () => ({
  getRefreshToken: () => getRefreshTokenMock(),
  setTokens: (...args: unknown[]) => setTokensMock(...args),
  setRoleCookie: (...args: unknown[]) => setRoleCookieMock(...args),
  clearTokens: () => clearTokensMock(),
}));

vi.mock("@/services/auth.service", () => ({
  getMe: () => getMeMock(),
  login: (...args: unknown[]) => loginRequestMock(...args),
  refreshToken: (...args: unknown[]) => refreshTokenRequestMock(...args),
  logout: () => logoutRequestMock(),
}));

function Probe() {
  const auth = useAuthContext();
  return (
    <div>
      <span data-testid="is-loading">{String(auth.isLoading)}</span>
      <span data-testid="is-authenticated">{String(auth.isAuthenticated)}</span>
      <span data-testid="email">{auth.user?.email ?? "none"}</span>
    </div>
  );
}

describe("AuthProvider", () => {
  it("restores authenticated state when refresh token exists", async () => {
    getRefreshTokenMock.mockReturnValueOnce("refresh-token");
    getMeMock.mockResolvedValueOnce({
      id: "00000000-0000-0000-0000-000000000001",
      email: "admin@example.com",
      is_active: true,
      roles: ["system_administrator"],
      created_at: "2026-01-01T00:00:00Z",
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("is-loading")).toHaveTextContent("false");
      expect(screen.getByTestId("is-authenticated")).toHaveTextContent("true");
      expect(screen.getByTestId("email")).toHaveTextContent("admin@example.com");
    });
  });
});

