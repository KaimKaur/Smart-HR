"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmployeeSearch } from "@/components/employees/employee-search";
import { FormField } from "@/components/common/form-field";
import { Button } from "@/components/ui/button";
import { createEmployeeSchema, updateEmployeeSchema } from "@/lib/validations";
import { listDepartments, listDesignations, listEmploymentStatuses } from "@/services/organization.service";
import type { Employee, ErrorResponse } from "@/types/api";
import { useApiQuery } from "@/hooks/use-api-query";

type CreateValues = z.infer<typeof createEmployeeSchema>;
type UpdateValues = z.infer<typeof updateEmployeeSchema>;

export function EmployeeForm({
  mode,
  initial,
  showSalary,
  onSubmit,
  onCancel,
  isSubmitting,
}: {
  mode: "create" | "edit";
  initial?: Employee;
  showSalary: boolean;
  onSubmit: (values: CreateValues | UpdateValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}) {
  const schema = mode === "create" ? createEmployeeSchema : updateEmployeeSchema;

  const departmentsQuery = useApiQuery({
    queryKey: ["departments", "all"],
    queryFn: () => listDepartments(1, 100),
  });
  const designationsQuery = useApiQuery({
    queryKey: ["designations", "all"],
    queryFn: () => listDesignations(1, 100),
  });
  const statusesQuery = useApiQuery({
    queryKey: ["employment-statuses"],
    queryFn: listEmploymentStatuses,
  });

  const form = useForm<CreateValues | UpdateValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      employee_code: "",
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
      department_id: "",
      designation_id: "",
      employment_status_id: "",
      manager_id: undefined,
      salary: undefined,
      join_date: "",
    },
  });

  useEffect(() => {
    if (!initial) return;
    form.reset({
      employee_code: initial.employee_code,
      first_name: initial.first_name,
      last_name: initial.last_name,
      email: initial.email,
      phone: initial.phone ?? "",
      department_id: initial.department?.id ?? "",
      designation_id: initial.designation?.id ?? "",
      employment_status_id: initial.employment_status?.id ?? "",
      manager_id: initial.manager?.id,
      salary: initial.salary ?? undefined,
      join_date: initial.join_date,
    });
  }, [initial, form]);

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      if (mode === "edit" && initial) {
        const dirty = form.formState.dirtyFields;
        const payload: UpdateValues = {};
        (Object.keys(dirty) as Array<keyof UpdateValues>).forEach((key) => {
          const value = values[key as keyof CreateValues];
          if (value !== undefined) {
            (payload as Record<string, unknown>)[key] = value === "" ? undefined : value;
          }
        });
        if (!Object.keys(payload).length) {
          onCancel();
          return;
        }
        await onSubmit(payload);
        return;
      }
      await onSubmit(values);
    } catch (err) {
      if (axios.isAxiosError<ErrorResponse>(err) && err.response?.data?.errors?.length) {
        err.response.data.errors.forEach((detail) => {
          if (detail.field) {
            form.setError(detail.field as keyof CreateValues, { message: detail.message });
          }
        });
      }
      throw err;
    }
  });

  const departments = departmentsQuery.data?.items ?? [];
  const designations = designationsQuery.data?.items ?? [];
  const statuses = statusesQuery.data ?? [];

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Employee code" required error={form.formState.errors.employee_code?.message}>
          <input
            className="h-9 w-full rounded-lg border bg-background px-3 text-sm"
            {...form.register("employee_code")}
          />
        </FormField>
        <FormField label="Join date" required error={form.formState.errors.join_date?.message}>
          <input type="date" className="h-9 w-full rounded-lg border bg-background px-3 text-sm" {...form.register("join_date")} />
        </FormField>
        <FormField label="First name" required error={form.formState.errors.first_name?.message}>
          <input className="h-9 w-full rounded-lg border bg-background px-3 text-sm" {...form.register("first_name")} />
        </FormField>
        <FormField label="Last name" required error={form.formState.errors.last_name?.message}>
          <input className="h-9 w-full rounded-lg border bg-background px-3 text-sm" {...form.register("last_name")} />
        </FormField>
        <FormField label="Email" required error={form.formState.errors.email?.message}>
          <input type="email" className="h-9 w-full rounded-lg border bg-background px-3 text-sm" {...form.register("email")} />
        </FormField>
        <FormField label="Phone" error={form.formState.errors.phone?.message}>
          <input className="h-9 w-full rounded-lg border bg-background px-3 text-sm" {...form.register("phone")} />
        </FormField>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Department" required error={form.formState.errors.department_id?.message}>
          <select className="h-9 w-full rounded-lg border bg-background px-3 text-sm" {...form.register("department_id")}>
            <option value="">Select department</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Designation" required error={form.formState.errors.designation_id?.message}>
          <select className="h-9 w-full rounded-lg border bg-background px-3 text-sm" {...form.register("designation_id")}>
            <option value="">Select designation</option>
            {designations.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Employment status" required error={form.formState.errors.employment_status_id?.message}>
          <select className="h-9 w-full rounded-lg border bg-background px-3 text-sm" {...form.register("employment_status_id")}>
            <option value="">Select status</option>
            {statuses.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </FormField>
        {showSalary ? (
          <FormField label="Salary" error={form.formState.errors.salary?.message}>
            <input
              type="number"
              min={0}
              step="0.01"
              className="h-9 w-full rounded-lg border bg-background px-3 text-sm"
              {...form.register("salary", { valueAsNumber: true })}
            />
          </FormField>
        ) : null}
      </div>

      <FormField label="Manager">
        <EmployeeSearch
          value={form.watch("manager_id") ?? null}
          onChange={(id) => form.setValue("manager_id", id ?? undefined, { shouldDirty: true })}
        />
      </FormField>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : mode === "create" ? "Create employee" : "Save changes"}
        </Button>
      </div>
    </form>
  );
}
