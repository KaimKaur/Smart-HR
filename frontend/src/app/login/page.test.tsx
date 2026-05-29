import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import LoginPage from "@/app/login/page";

const replaceMock = vi.fn();
const loginMock = vi.fn();
const toastSuccessMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ success: toastSuccessMock, error: vi.fn(), info: vi.fn() }),
}));

vi.mock("@/providers/auth-provider", () => ({
  useAuthContext: () => ({
    login: loginMock,
    user: null,
    isLoading: false,
  }),
}));

describe("LoginPage", () => {
  it("renders and submits credentials", async () => {
    loginMock.mockResolvedValueOnce({ roles: ["employee"] });

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "employee@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith("employee@example.com", "password123");
      expect(replaceMock).toHaveBeenCalledWith("/employee/dashboard");
    });
  });
});

