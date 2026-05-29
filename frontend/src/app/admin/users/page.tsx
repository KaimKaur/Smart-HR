"use client";

import axios from "axios";
import { Eye, EyeOff } from "lucide-react";
import { useMemo, useState } from "react";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { DataTable, type DataTableColumn } from "@/components/common/data-table";
import { FormField } from "@/components/common/form-field";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { useAssignRole, useCreateUser, useDeactivateUser, useUsers } from "@/hooks/use-admin";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import type { ErrorResponse } from "@/types/api";
import type { AdminUser } from "@/services/admin-user.service";

const ROLE_OPTIONS = [
  "system_administrator",
  "hr_manager",
  "recruiter",
  "department_manager",
  "employee",
] as const;

export default function AdminUsersPage() {
  const { hasRole } = useAuth();
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [roleTarget, setRoleTarget] = useState<AdminUser | null>(null);
  const [deactivateTarget, setDeactivateTarget] = useState<AdminUser | null>(null);
  const usersQuery = useUsers({ search: search || undefined, page, page_size: 20 });
  const createMutation = useCreateUser();
  const deactivateMutation = useDeactivateUser();

  const columns: DataTableColumn<AdminUser>[] = useMemo(
    () => [
      { key: "email", header: "Email", render: (row) => row.email },
      { key: "active", header: "Status", render: (row) => (row.is_active ? "Active" : "Inactive") },
      {
        key: "roles",
        header: "Roles",
        render: (row) => row.roles.join(", ") || "—",
      },
      {
        key: "actions",
        header: "Actions",
        render: (row) => (
          <div className="flex gap-2">
            <Button type="button" size="sm" variant="outline" onClick={() => setRoleTarget(row)}>
              Assign roles
            </Button>
            <Button type="button" size="sm" variant="destructive" onClick={() => setDeactivateTarget(row)}>
              Deactivate
            </Button>
          </div>
        ),
      },
    ],
    [],
  );

  if (!hasRole("system_administrator")) {
    return (
      <div className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">
        System Administrator access is required.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Users"
        description="Manage users, create accounts, and assign roles."
        action={
          <Button type="button" onClick={() => setShowCreate(true)}>
            Create user
          </Button>
        }
      />

      <div className="rounded-xl border bg-card p-4">
        <FormField label="Search users">
          <input
            className="h-9 w-full rounded-lg border px-3 text-sm"
            placeholder="Search by email"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        </FormField>
      </div>

      <DataTable
        columns={columns}
        rows={usersQuery.data?.items ?? []}
        isLoading={usersQuery.isLoading}
        getRowKey={(row) => row.id}
        emptyTitle="No users found"
      />

      {usersQuery.data?.pagination ? (
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" disabled={page <= 1} onClick={() => setPage((v) => v - 1)}>
            Previous
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={page >= usersQuery.data.pagination.total_pages}
            onClick={() => setPage((v) => v + 1)}
          >
            Next
          </Button>
        </div>
      ) : null}

      {showCreate ? (
        <CreateUserModal
          isSubmitting={createMutation.isPending}
          onCancel={() => setShowCreate(false)}
          onSubmit={async ({ email, roles }) => {
            try {
              await createMutation.mutateAsync({ email, roles, is_active: true });
              toast.success("User created.");
              setShowCreate(false);
              await usersQuery.refetch();
            } catch (error) {
              const message = axios.isAxiosError<ErrorResponse>(error)
                ? error.response?.data?.message
                : "Unable to create user.";
              toast.error(message ?? "Unable to create user.");
            }
          }}
        />
      ) : null}

      {roleTarget ? (
        <AssignRolesModal
          user={roleTarget}
          onCancel={() => setRoleTarget(null)}
          onSuccess={() => void usersQuery.refetch()}
        />
      ) : null}

      {deactivateTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <ConfirmDialog
            title="Deactivate user"
            description={`Deactivate ${deactivateTarget.email}?`}
            confirmText="Deactivate"
            onCancel={() => setDeactivateTarget(null)}
            onConfirm={async () => {
              await deactivateMutation.mutateAsync(deactivateTarget.id);
              toast.success("User deactivated.");
              setDeactivateTarget(null);
              await usersQuery.refetch();
            }}
          />
        </div>
      ) : null}
    </div>
  );
}

function CreateUserModal({
  onCancel,
  onSubmit,
  isSubmitting,
}: {
  onCancel: () => void;
  onSubmit: (payload: { email: string; roles: string[]; password?: string }) => Promise<void>;
  isSubmitting?: boolean;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [roles, setRoles] = useState<string[]>(["employee"]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        className="w-full max-w-lg space-y-4 rounded-xl border bg-background p-6"
        onSubmit={async (event) => {
          event.preventDefault();
          await onSubmit({ email, roles, password });
        }}
      >
        <h2 className="text-lg font-semibold">Create user</h2>
        <FormField label="Email" required>
          <input
            type="email"
            className="h-9 w-full rounded-lg border px-3 text-sm"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </FormField>
        <FormField label="Password" required>
          <div className="flex gap-2">
            <input
              type={showPassword ? "text" : "password"}
              className="h-9 w-full rounded-lg border px-3 text-sm"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <Button type="button" variant="outline" onClick={() => setShowPassword((v) => !v)}>
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Password field is kept for UX parity; backend currently returns a reset-token onboarding flow.
          </p>
        </FormField>
        <FormField label="Roles">
          <div className="grid gap-2 sm:grid-cols-2">
            {ROLE_OPTIONS.map((role) => (
              <label key={role} className="inline-flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={roles.includes(role)}
                  onChange={(event) => {
                    setRoles((current) =>
                      event.target.checked
                        ? [...current, role]
                        : current.filter((r) => r !== role),
                    );
                  }}
                />
                {role}
              </label>
            ))}
          </div>
        </FormField>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            Create
          </Button>
        </div>
      </form>
    </div>
  );
}

function AssignRolesModal({
  user,
  onCancel,
  onSuccess,
}: {
  user: AdminUser;
  onCancel: () => void;
  onSuccess: () => void;
}) {
  const toast = useToast();
  const assignRole = useAssignRole(user.id);
  const [selectedRoles, setSelectedRoles] = useState<string[]>(user.roles);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <form
        className="w-full max-w-lg space-y-4 rounded-xl border bg-background p-6"
        onSubmit={async (event) => {
          event.preventDefault();
          const missing = selectedRoles.filter((role) => !user.roles.includes(role));
          await Promise.all(missing.map((role) => assignRole.mutateAsync(role)));
          toast.success("Roles updated.");
          onCancel();
          onSuccess();
        }}
      >
        <h2 className="text-lg font-semibold">Assign roles</h2>
        <p className="text-sm text-muted-foreground">{user.email}</p>
        <div className="grid gap-2 sm:grid-cols-2">
          {ROLE_OPTIONS.map((role) => (
            <label key={role} className="inline-flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={selectedRoles.includes(role)}
                onChange={(event) =>
                  setSelectedRoles((current) =>
                    event.target.checked
                      ? [...current, role]
                      : current.filter((r) => r !== role),
                  )
                }
              />
              {role}
            </label>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          Role removal requires role IDs; current backend user response exposes role slugs only. This UI adds new roles.
        </p>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={assignRole.isPending}>
            Save roles
          </Button>
        </div>
      </form>
    </div>
  );
}

