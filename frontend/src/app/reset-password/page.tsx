"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/common/form-field";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { resetPasswordSchema } from "@/lib/validations";
import { resetPassword } from "@/services/auth.service";
import type { ErrorResponse } from "@/types/api";

type ResetPasswordFormValues = {
  token: string;
  new_password: string;
  confirm_password: string;
};

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [formError, setFormError] = useState<string | null>(null);

  const tokenFromQuery = searchParams.get("token") ?? "";

  const defaultValues = useMemo<ResetPasswordFormValues>(
    () => ({
      token: tokenFromQuery,
      new_password: "",
      confirm_password: "",
    }),
    [tokenFromQuery],
  );

  const form = useForm<ResetPasswordFormValues>({
    defaultValues,
    resolver: zodResolver(resetPasswordSchema),
    mode: "onSubmit",
  });

  useEffect(() => {
    form.setValue("token", tokenFromQuery);
  }, [tokenFromQuery, form]);

  const onSubmit = form.handleSubmit(async (values) => {
    setFormError(null);
    try {
      await resetPassword({ token: values.token, new_password: values.new_password });
      toast.success("Password reset successful. Please sign in.");
      router.replace("/login");
    } catch (err) {
      let message = "Unable to reset password. Please try again.";
      if (axios.isAxiosError<ErrorResponse>(err)) {
        message = err.response?.data?.message ?? message;
        if (message.toLowerCase().includes("expired")) {
          message = "This reset token has expired. Request a new one.";
        }
      }
      setFormError(message);
    }
  });

  const submitting = form.formState.isSubmitting;

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md rounded-xl border bg-card p-6 shadow-sm">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Reset password</h1>
          <p className="text-sm text-muted-foreground">Set a new password for your account.</p>
        </div>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <FormField label="Reset token" required error={form.formState.errors.token?.message}>
            <input
              type="text"
              className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              {...form.register("token")}
            />
          </FormField>

          <FormField label="New password" required error={form.formState.errors.new_password?.message}>
            <input
              type="password"
              autoComplete="new-password"
              className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              {...form.register("new_password")}
            />
          </FormField>

          <FormField
            label="Confirm new password"
            required
            error={form.formState.errors.confirm_password?.message}
          >
            <input
              type="password"
              autoComplete="new-password"
              className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              {...form.register("confirm_password")}
            />
          </FormField>

          {formError ? (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {formError}
            </div>
          ) : null}

          <Button className="w-full" disabled={submitting} type="submit">
            {submitting ? "Resetting..." : "Reset password"}
          </Button>

          <div className="flex justify-between text-sm">
            <Link className="text-primary hover:underline" href="/forgot-password">
              Request new token
            </Link>
            <Link className="text-primary hover:underline" href="/login">
              Back to login
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

