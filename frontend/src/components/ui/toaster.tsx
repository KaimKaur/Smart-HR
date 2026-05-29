"use client";

import { cn } from "@/lib/utils";
import { useToastContext } from "@/providers/toast-provider";

const tone = {
  success: "border-green-500/50 bg-green-50 text-green-900",
  error: "border-red-500/50 bg-red-50 text-red-900",
  info: "border-blue-500/50 bg-blue-50 text-blue-900",
} as const;

export function Toaster() {
  const { toasts, removeToast } = useToastContext();

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-80 flex-col gap-2">
      {toasts.map((toast) => (
        <button
          key={toast.id}
          type="button"
          onClick={() => removeToast(toast.id)}
          className={cn(
            "pointer-events-auto rounded-md border p-3 text-left shadow-sm transition hover:opacity-90",
            tone[toast.variant],
          )}
        >
          {toast.title ? <p className="text-sm font-semibold">{toast.title}</p> : null}
          <p className="text-sm">{toast.message}</p>
        </button>
      ))}
    </div>
  );
}
