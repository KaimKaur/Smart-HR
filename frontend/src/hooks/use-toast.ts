"use client";

import { useToastContext } from "@/providers/toast-provider";

export function useToast() {
  const { pushToast } = useToastContext();

  return {
    success: (message: string, title = "Success") =>
      pushToast({ message, title, variant: "success" }),
    error: (message: string, title = "Error") =>
      pushToast({ message, title, variant: "error" }),
    info: (message: string, title = "Info") =>
      pushToast({ message, title, variant: "info" }),
  };
}
