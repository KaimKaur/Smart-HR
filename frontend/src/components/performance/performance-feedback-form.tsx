"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormField } from "@/components/common/form-field";
import { Button } from "@/components/ui/button";
import { useAddFeedback, useFeedback } from "@/hooks/use-performance";
import { useToast } from "@/hooks/use-toast";
import { performanceFeedbackSchema } from "@/lib/validations";

type FeedbackFormValues = z.infer<typeof performanceFeedbackSchema>;

export function PerformanceFeedbackForm({ reviewId }: { reviewId: string }) {
  const toast = useToast();
  const feedbackQuery = useFeedback(reviewId);
  const addFeedbackMutation = useAddFeedback();

  const form = useForm<FeedbackFormValues>({
    resolver: zodResolver(performanceFeedbackSchema),
    defaultValues: { feedback_text: "" },
  });

  return (
    <section className="space-y-4 rounded-xl border bg-card p-4">
      <h3 className="text-base font-semibold">Feedback</h3>
      <form
        className="space-y-3"
        onSubmit={form.handleSubmit(async (values) => {
          await addFeedbackMutation.mutateAsync({ reviewId, payload: values });
          toast.success("Feedback submitted.");
          form.reset();
          await feedbackQuery.refetch();
        })}
      >
        <FormField label="Your feedback" required error={form.formState.errors.feedback_text?.message}>
          <textarea
            rows={4}
            maxLength={5000}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            placeholder="Share constructive feedback (max 5000 characters)"
            {...form.register("feedback_text")}
          />
        </FormField>
        <Button type="submit" disabled={addFeedbackMutation.isPending}>
          {addFeedbackMutation.isPending ? "Submitting..." : "Submit feedback"}
        </Button>
      </form>

      <ul className="space-y-3">
        {(feedbackQuery.data ?? []).map((entry) => (
          <li key={entry.id} className="rounded-lg border p-3">
            <p className="text-sm">{entry.feedback_text}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              {entry.author?.full_name ?? "Unknown"} · {new Date(entry.created_at).toLocaleString()}
            </p>
          </li>
        ))}
        {!feedbackQuery.isLoading && !(feedbackQuery.data ?? []).length ? (
          <p className="text-sm text-muted-foreground">No feedback yet.</p>
        ) : null}
      </ul>
    </section>
  );
}
