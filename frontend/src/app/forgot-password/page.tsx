"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import Link from "next/link";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { FormField } from "@/components/common/form-field";
import { forgotPasswordSchema } from "@/lib/validations";
import { useToast } from "@/hooks/use-toast";
import { forgotPassword } from "@/services/auth.service";
import type { ErrorResponse } from "@/types/api";

type ForgotPasswordFormValues = {
  email: string;
};

export default function ForgotPasswordPage() {
  const toast = useToast();
  const [submitted, setSubmitted] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const defaultValues = useMemo<ForgotPasswordFormValues>(() => ({ email: "" }), []);

  const form = useForm<ForgotPasswordFormValues>({
    defaultValues,
    resolver: zodResolver(forgotPasswordSchema),
    mode: "onSubmit",
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setFormError(null);
    try {
      await forgotPassword({ email: values.email });
    } catch (err) {
      // Security: always show success message, but keep a non-blocking toast for unexpected errors.
      if (axios.isAxiosError<ErrorResponse>(err) && err.response?.data?.message) {
        toast.info(err.response.data.message);
      } else {
        toast.info("Request received.");
      }
    } finally {
      setSubmitted(true);
    }
  });

  const submitting = form.formState.isSubmitting;

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md rounded-xl border bg-card p-6 shadow-sm">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Forgot password</h1>
          <p className="text-sm text-muted-foreground">
            {submitted
              ? "If this email exists, you'll receive instructions to reset your password."
              : "Enter your email and we’ll send reset instructions if the account exists."}
          </p>
        </div>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <FormField label="Email" required error={form.formState.errors.email?.message}>
            <input
              type="email"
              autoComplete="email"
              className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              disabled={submitted}
              {...form.register("email")}
            />
          </FormField>

          {formError ? (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {formError}
            </div>
          ) : null}

          <Button className="w-full" disabled={submitted || submitting} type="submit">
            {submitted ? "Email sent" : submitting ? "Sending..." : "Send reset link"}
          </Button>

          <div className="flex justify-between text-sm">
            <Link className="text-primary hover:underline" href="/login">
              Back to login
            </Link>
            <Link className="text-primary hover:underline" href="/reset-password">
              Have a token?
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

