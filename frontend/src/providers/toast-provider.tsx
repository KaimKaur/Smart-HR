"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

type ToastVariant = "success" | "error" | "info";

export interface ToastItem {
  id: string;
  title?: string;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toasts: ToastItem[];
  pushToast: (toast: Omit<ToastItem, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const pushToast = useCallback((toast: Omit<ToastItem, "id">) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { ...toast, id }]);
    window.setTimeout(() => removeToast(id), 5000);
  }, [removeToast]);

  const value = useMemo(
    () => ({ toasts, pushToast, removeToast }),
    [toasts, pushToast, removeToast],
  );

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToastContext() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToastContext must be used within ToastProvider");
  }
  return context;
}
