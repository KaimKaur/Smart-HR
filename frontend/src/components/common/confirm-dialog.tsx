"use client";

import { Button } from "@/components/ui/button";

export function ConfirmDialog({
  title,
  description,
  onConfirm,
  onCancel,
  confirmText = "Confirm",
}: {
  title: string;
  description: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmText?: string;
}) {
  return (
    <div className="rounded-lg border bg-background p-4 shadow-md">
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <div className="mt-4 flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="button" onClick={onConfirm}>
          {confirmText}
        </Button>
      </div>
    </div>
  );
}
