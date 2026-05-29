"use client";

import Link from "next/link";
import { useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { FormField } from "@/components/common/form-field";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { useAuditLogs } from "@/hooks/use-admin";
import { useAuth } from "@/hooks/useAuth";
import type { AuditLog } from "@/types/api";

export default function AuditLogsPage() {
  const { hasRole } = useAuth();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    actor_user_id: "",
    action: "",
    resource_type: "",
    search: "",
    date_from: "",
    date_to: "",
    page: 1,
  });

  const query = useAuditLogs({
    actor_user_id: filters.actor_user_id || undefined,
    action: filters.action || undefined,
    resource_type: filters.resource_type || undefined,
    search: filters.search || undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    page: filters.page,
    page_size: 20,
  });

  if (!hasRole("system_administrator")) {
    return (
      <div className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">
        System Administrator access is required.
      </div>
    );
  }

  const columns: DataTableColumn<AuditLog>[] = [
    {
      key: "actor",
      header: "Actor",
      render: (row) =>
        row.actor_user_id ? (
          <Link className="text-primary hover:underline" href={`/admin/users?actor=${row.actor_user_id}`}>
            {row.actor_user_id}
          </Link>
        ) : (
          "—"
        ),
    },
    { key: "action", header: "Action", render: (row) => row.action },
    { key: "resource", header: "Resource", render: (row) => row.resource_type },
    { key: "resource_id", header: "Resource ID", render: (row) => row.resource_id ?? "—" },
    { key: "ip", header: "IP", render: (row) => row.ip_address },
    { key: "time", header: "Time", render: (row) => new Date(row.created_at).toLocaleString() },
    {
      key: "detail",
      header: "",
      render: (row) => (
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => setExpandedId((id) => (id === row.id ? null : row.id))}
        >
          {expandedId === row.id ? "Hide" : "Detail"}
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Audit logs" description="Filter and inspect system audit events." />

      <div className="grid gap-3 rounded-xl border bg-card p-4 sm:grid-cols-2 lg:grid-cols-3">
        <FormField label="Actor user ID">
          <input
            className="h-9 rounded-lg border px-3 text-sm"
            value={filters.actor_user_id}
            onChange={(event) => setFilters((s) => ({ ...s, actor_user_id: event.target.value, page: 1 }))}
          />
        </FormField>
        <FormField label="Action">
          <input
            className="h-9 rounded-lg border px-3 text-sm"
            value={filters.action}
            onChange={(event) => setFilters((s) => ({ ...s, action: event.target.value, page: 1 }))}
          />
        </FormField>
        <FormField label="Resource type">
          <input
            className="h-9 rounded-lg border px-3 text-sm"
            value={filters.resource_type}
            onChange={(event) => setFilters((s) => ({ ...s, resource_type: event.target.value, page: 1 }))}
          />
        </FormField>
        <FormField label="Search">
          <input
            className="h-9 rounded-lg border px-3 text-sm"
            value={filters.search}
            onChange={(event) => setFilters((s) => ({ ...s, search: event.target.value, page: 1 }))}
          />
        </FormField>
        <FormField label="From">
          <input
            type="date"
            className="h-9 rounded-lg border px-3 text-sm"
            value={filters.date_from}
            onChange={(event) => setFilters((s) => ({ ...s, date_from: event.target.value, page: 1 }))}
          />
        </FormField>
        <FormField label="To">
          <input
            type="date"
            className="h-9 rounded-lg border px-3 text-sm"
            value={filters.date_to}
            onChange={(event) => setFilters((s) => ({ ...s, date_to: event.target.value, page: 1 }))}
          />
        </FormField>
      </div>

      <DataTable
        columns={columns}
        rows={query.data?.items ?? []}
        isLoading={query.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No audit logs"
      />

      {expandedId ? (
        <AuditDetailModal
          item={(query.data?.items ?? []).find((item) => item.id === expandedId) ?? null}
          onClose={() => setExpandedId(null)}
        />
      ) : null}

      {query.data?.pagination ? (
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            disabled={filters.page <= 1}
            onClick={() => setFilters((s) => ({ ...s, page: s.page - 1 }))}
          >
            Previous
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={filters.page >= query.data.pagination.total_pages}
            onClick={() => setFilters((s) => ({ ...s, page: s.page + 1 }))}
          >
            Next
          </Button>
        </div>
      ) : null}
    </div>
  );
}

function AuditDetailModal({ item, onClose }: { item: AuditLog | null; onClose: () => void }) {
  if (!item) return null;

  const beforeJson = JSON.stringify(item.before_state ?? {}, null, 2);
  const afterJson = JSON.stringify(item.after_state ?? {}, null, 2);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-5xl space-y-4 rounded-xl border bg-background p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Audit log detail</h2>
            <p className="text-sm text-muted-foreground">
              {item.action} · {item.resource_type} · IP {item.ip_address}
            </p>
          </div>
          <Button type="button" variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border p-3">
            <p className="mb-2 text-sm font-medium">Before state</p>
            <pre className="max-h-96 overflow-auto rounded bg-muted/30 p-2 text-xs">{beforeJson}</pre>
          </div>
          <div className="rounded-lg border p-3">
            <p className="mb-2 text-sm font-medium">After state</p>
            <pre className="max-h-96 overflow-auto rounded bg-muted/30 p-2 text-xs">{afterJson}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}

