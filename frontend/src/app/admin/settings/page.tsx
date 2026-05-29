"use client";

import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";

export default function AdminSettingsPage() {
  const { hasRole } = useAuth();
  const toast = useToast();
  const appVersion = process.env.NEXT_PUBLIC_APP_VERSION ?? "dev";

  if (!hasRole("system_administrator")) {
    return (
      <div className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">
        System Administrator access is required.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="System settings" description="Administrative settings (MVP stub)." />

      <section className="rounded-xl border bg-card p-4">
        <h2 className="text-base font-semibold">Environment</h2>
        <p className="mt-2 text-sm text-muted-foreground">App version: {appVersion}</p>
      </section>

      <section className="rounded-xl border bg-card p-4">
        <h2 className="text-base font-semibold">Seed data</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Re-run seed is a development-only placeholder in this UI.
        </p>
        <Button
          type="button"
          className="mt-3"
          variant="outline"
          onClick={() => toast.info("Seed re-run is not wired in frontend yet.")}
        >
          Re-run seed data
        </Button>
      </section>
    </div>
  );
}

