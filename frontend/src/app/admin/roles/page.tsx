"use client";

import { useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { useAuth } from "@/hooks/useAuth";

type RoleRow = {
  slug: string;
  name: string;
  description: string;
  permissions: string[];
};

const ROLE_DEFINITIONS: RoleRow[] = [
  {
    slug: "system_administrator",
    name: "System Administrator",
    description: "Full platform administration access.",
    permissions: ["users:create", "users:update", "audit_logs:read", "settings:update", "all:*"],
  },
  {
    slug: "hr_manager",
    name: "HR Manager",
    description: "Manages HR modules and operations.",
    permissions: ["employees:*", "attendance:*", "leave:*", "performance:*", "reports:*"],
  },
  {
    slug: "recruiter",
    name: "Recruiter",
    description: "Manages recruitment pipeline and interviews.",
    permissions: ["jobs:read", "candidates:*", "interviews:*", "applications:*"],
  },
  {
    slug: "department_manager",
    name: "Department Manager",
    description: "Access to team-level workflows and approvals.",
    permissions: ["team:read", "leave:approve", "performance:team_read"],
  },
  {
    slug: "employee",
    name: "Employee",
    description: "Self-service access for personal workflows.",
    permissions: ["self:attendance", "self:leave", "self:performance", "notifications:read"],
  },
];

export default function AdminRolesPage() {
  const { hasRole } = useAuth();
  const [selected, setSelected] = useState<RoleRow | null>(ROLE_DEFINITIONS[0]);

  if (!hasRole("system_administrator")) {
    return (
      <div className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">
        System Administrator access is required.
      </div>
    );
  }

  const columns: DataTableColumn<RoleRow>[] = [
    { key: "name", header: "Role", render: (row) => row.name },
    { key: "desc", header: "Description", render: (row) => row.description },
    { key: "count", header: "Permission count", render: (row) => row.permissions.length },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Roles"
        description="Read-only role catalog and permission definitions."
      />

      <DataTable
        columns={columns}
        rows={ROLE_DEFINITIONS}
        getRowKey={(row) => row.slug}
        onRowClick={(row) => setSelected(row)}
      />

      {selected ? (
        <section className="rounded-xl border bg-card p-4">
          <h2 className="text-base font-semibold">{selected.name}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{selected.description}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {selected.permissions.map((permission) => (
              <span key={permission} className="rounded-full border px-2 py-0.5 text-xs">
                {permission}
              </span>
            ))}
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Role list endpoint is not currently exposed by backend API; this view reflects seeded role conventions.
          </p>
        </section>
      ) : null}
    </div>
  );
}

