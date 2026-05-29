"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormField } from "@/components/common/form-field";
import { Button } from "@/components/ui/button";
import { useCreateCorrection } from "@/hooks/use-attendance";
import { useToast } from "@/hooks/use-toast";
import { correctionRequestSchema } from "@/lib/validations";

type CorrectionFormValues = z.infer<typeof correctionRequestSchema>;

export function CorrectionRequestDialog({
  recordId,
  onClose,
  onSuccess,
}: {
  recordId: string;
  onClose: () => void;
  onSuccess?: () => void;
}) {
  const toast = useToast();
  const createCorrection = useCreateCorrection();

  const form = useForm<CorrectionFormValues>({
    resolver: zodResolver(correctionRequestSchema),
    defaultValues: { reason: "" },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        className="w-full max-w-md space-y-4 rounded-xl border bg-background p-6"
        onSubmit={form.handleSubmit(async (values) => {
          await createCorrection.mutateAsync({ recordId, reason: values.reason });
          toast.success("Correction request submitted.");
          onSuccess?.();
          onClose();
        })}
      >
        <h2 className="text-lg font-semibold">Request correction</h2>
        <FormField label="Reason" required error={form.formState.errors.reason?.message}>
          <textarea rows={4} className="w-full rounded-lg border px-3 py-2 text-sm" {...form.register("reason")} />
        </FormField>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={createCorrection.isPending}>
            {createCorrection.isPending ? "Submitting..." : "Submit request"}
          </Button>
        </div>
      </form>
    </div>
  );
}
