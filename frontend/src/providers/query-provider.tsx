"use client";

import { QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { useToast } from "@/hooks/use-toast";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const toast = useToast();
  const [client] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onError: (error) => {
            toast.error(error instanceof Error ? error.message : "Unexpected server error");
          },
        }),
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
          },
        },
      }),
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
