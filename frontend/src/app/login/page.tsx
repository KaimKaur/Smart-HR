"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { DEFAULT_DASHBOARD_BY_ROLE } from "@/constants/routes";
import { FormField } from "@/components/common/form-field";
import { loginSchema } from "@/lib/validations";
import { useToast } from "@/hooks/use-toast";
import { useAuthContext } from "@/providers/auth-provider";
import type { ErrorResponse, RoleSlug } from "@/types/api";

type LoginFormValues = {
  email: string;
  password: string;
};

const ROLE_PRIORITY: RoleSlug[] = [
  "system_administrator",
  "hr_manager",
  "recruiter",
  "department_manager",
  "employee",
];

function getDashboardForRoles(roles: RoleSlug[]): string {
  const matched = ROLE_PRIORITY.find((role) => roles.includes(role));
  if (!matched) return "/employee/dashboard";
  return DEFAULT_DASHBOARD_BY_ROLE[matched];
}

export default function LoginPage() {
  const router = useRouter();
  const toast = useToast();
  const { login, user, isLoading } = useAuthContext();
  const [formError, setFormError] = useState<string | null>(null);

  const defaultValues = useMemo<LoginFormValues>(
    () => ({
      email: "",
      password: "",
    }),
    [],
  );

  const form = useForm<LoginFormValues>({
    defaultValues,
    resolver: zodResolver(loginSchema),
    mode: "onSubmit",
  });

  useEffect(() => {
    if (isLoading) return;
    if (!user) return;
    router.replace(getDashboardForRoles(user.roles));
  }, [isLoading, user, router]);

  const onSubmit = form.handleSubmit(async (values) => {
    setFormError(null);
    try {
      const me = await login(values.email, values.password);
      toast.success("Welcome back.");
      router.replace(getDashboardForRoles(me.roles));
    } catch (err) {
      let message = "Unable to sign in. Please try again.";
      if (axios.isAxiosError<ErrorResponse>(err)) {
        message = err.response?.data?.message ?? message;
        if (err.response?.status === 401) {
          message = "Invalid email or password.";
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
          <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
          <p className="text-sm text-muted-foreground">
            Enter your email and password to access Smart HR.
          </p>
        </div>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <FormField
            label="Email"
            required
            error={form.formState.errors.email?.message}
          >
            <input
              type="email"
              autoComplete="email"
              className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              {...form.register("email")}
            />
          </FormField>

          <FormField
            label="Password"
            required
            error={form.formState.errors.password?.message}
          >
            <input
              type="password"
              autoComplete="current-password"
              className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              {...form.register("password")}
            />
          </FormField>

          {formError ? (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {formError}
            </div>
          ) : null}

          <Button className="w-full" disabled={submitting} type="submit">
            {submitting ? "Signing in..." : "Sign in"}
          </Button>

          <div className="flex justify-end">
            <Link className="text-sm text-primary hover:underline" href="/forgot-password">
              Forgot password?
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

