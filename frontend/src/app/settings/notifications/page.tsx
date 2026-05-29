"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import {
  useNotificationPreferences,
  useUpdateNotificationPreferences,
} from "@/hooks/use-notifications";
import { useToast } from "@/hooks/use-toast";

export default function NotificationSettingsPage() {
  const toast = useToast();
  const preferencesQuery = useNotificationPreferences();
  const updatePreferences = useUpdateNotificationPreferences();
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    if (preferencesQuery.data) {
      setEnabled(preferencesQuery.data.in_app_enabled);
    }
  }, [preferencesQuery.data]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notification preferences"
        description="Configure in-app notification behavior."
      />

      <section className="max-w-xl rounded-xl border bg-card p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium">In-app notifications</p>
            <p className="text-sm text-muted-foreground">
              Enable or disable notifications inside the app.
            </p>
          </div>
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(event) => setEnabled(event.target.checked)}
            />
            {enabled ? "Enabled" : "Disabled"}
          </label>
        </div>
        <div className="mt-4">
          <Button
            type="button"
            disabled={updatePreferences.isPending}
            onClick={async () => {
              await updatePreferences.mutateAsync({ in_app_enabled: enabled });
              toast.success("Notification preference saved.");
            }}
          >
            Save preferences
          </Button>
        </div>
      </section>
    </div>
  );
}

