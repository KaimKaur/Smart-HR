import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement } from "react";

import { AuthProvider } from "@/providers/auth-provider";

function makeClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

export function renderWithProviders(ui: ReactElement, options?: RenderOptions) {
  const queryClient = makeClient();
  return render(
    <AuthProvider>
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    </AuthProvider>,
    options,
  );
}

