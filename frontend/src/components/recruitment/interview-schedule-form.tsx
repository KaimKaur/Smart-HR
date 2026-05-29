"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmployeeSearch } from "@/components/employees/employee-search";
import { FormField } from "@/components/common/form-field";
import { Button } from "@/components/ui/button";
import { useScheduleInterview } from "@/hooks/use-interviews";
import { useToast } from "@/hooks/use-toast";
import { scheduleInterviewSchema } from "@/lib/validations";

type ScheduleFormValues = z.infer<typeof scheduleInterviewSchema>;

export function InterviewScheduleForm({
  applicationId,
  onSuccess,
  onCancel,
}: {
  applicationId: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}) {
  const toast = useToast();
  const scheduleMutation = useScheduleInterview();

  const form = useForm<ScheduleFormValues>({
    resolver: zodResolver(scheduleInterviewSchema),
    defaultValues: {
      application_id: applicationId,
      scheduled_at: "",
      interviewer_id: undefined,
      notes: "",
    },
  });

  return (
    <form
      className="space-y-4"
      onSubmit={form.handleSubmit(async (values) => {
        const scheduled = new Date(values.scheduled_at);
        if (scheduled <= new Date()) {
          form.setError("scheduled_at", { message: "Interview must be scheduled in the future" });
          return;
        }
        await scheduleMutation.mutateAsync({
          application_id: values.application_id,
          scheduled_at: scheduled.toISOString(),
          interviewer_id: values.interviewer_id,
          notes: values.notes,
        });
        toast.success("Interview scheduled.");
        onSuccess?.();
      })}
    >
      <FormField label="Date & time" required error={form.formState.errors.scheduled_at?.message}>
        <input
          type="datetime-local"
          className="h-9 w-full rounded-lg border px-3 text-sm"
          {...form.register("scheduled_at")}
        />
      </FormField>

      <FormField label="Interviewer">
        <EmployeeSearch
          value={form.watch("interviewer_id") ?? null}
          onChange={(id) => form.setValue("interviewer_id", id ?? undefined)}
        />
      </FormField>

      <FormField label="Notes" error={form.formState.errors.notes?.message}>
        <textarea rows={3} className="w-full rounded-lg border px-3 py-2 text-sm" {...form.register("notes")} />
      </FormField>

      <div className="flex justify-end gap-2">
        {onCancel ? (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        ) : null}
        <Button type="submit" disabled={scheduleMutation.isPending}>
          {scheduleMutation.isPending ? "Scheduling..." : "Schedule interview"}
        </Button>
      </div>
    </form>
  );
}
