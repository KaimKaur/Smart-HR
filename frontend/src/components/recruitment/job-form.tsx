"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormField } from "@/components/common/form-field";
import { Button } from "@/components/ui/button";
import { useApiQuery } from "@/hooks/use-api-query";
import { createJobSchema } from "@/lib/validations";
import { listDepartments } from "@/services/organization.service";
import type { Job } from "@/types/api";

type JobFormValues = z.infer<typeof createJobSchema>;

export function JobForm({
  mode,
  initial,
  onSubmit,
  onCancel,
  isSubmitting,
}: {
  mode: "create" | "edit";
  initial?: Job;
  onSubmit: (values: JobFormValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}) {
  const [skillInput, setSkillInput] = useState("");
  const departmentsQuery = useApiQuery({
    queryKey: ["departments", "all"],
    queryFn: () => listDepartments(1, 100),
  });

  const form = useForm<JobFormValues>({
    resolver: zodResolver(createJobSchema),
    defaultValues: {
      title: "",
      department_id: undefined,
      description: "",
      skills: [],
    },
  });

  useEffect(() => {
    if (!initial) return;
    form.reset({
      title: initial.title,
      department_id: initial.department_id ?? undefined,
      description: initial.description,
      skills: initial.skills,
    });
  }, [initial, form]);

  const skills = form.watch("skills") ?? [];

  const addSkill = () => {
    const trimmed = skillInput.trim();
    if (!trimmed || skills.includes(trimmed)) return;
    form.setValue("skills", [...skills, trimmed], { shouldDirty: true });
    setSkillInput("");
  };

  return (
    <form
      className="space-y-4"
      onSubmit={form.handleSubmit(async (values) => {
        if (mode === "edit" && initial) {
          const dirty = form.formState.dirtyFields;
          const payload: Partial<JobFormValues> = {};
          (Object.keys(dirty) as Array<keyof JobFormValues>).forEach((key) => {
            payload[key] = values[key] as never;
          });
          if (!Object.keys(payload).length) {
            onCancel();
            return;
          }
          await onSubmit(payload as JobFormValues);
          return;
        }
        await onSubmit(values);
      })}
    >
      <FormField label="Title" required error={form.formState.errors.title?.message}>
        <input className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("title")} />
      </FormField>

      <FormField label="Department" error={form.formState.errors.department_id?.message}>
        <select className="h-9 w-full rounded-lg border px-3 text-sm" {...form.register("department_id")}>
          <option value="">Select department</option>
          {(departmentsQuery.data?.items ?? []).map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </FormField>

      <FormField label="Description" required error={form.formState.errors.description?.message}>
        <textarea
          rows={4}
          className="w-full rounded-lg border px-3 py-2 text-sm"
          {...form.register("description")}
        />
      </FormField>

      <div className="space-y-2">
        <label className="text-sm font-medium">Skills</label>
        <div className="flex gap-2">
          <input
            className="h-9 flex-1 rounded-lg border px-3 text-sm"
            value={skillInput}
            onChange={(event) => setSkillInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                addSkill();
              }
            }}
            placeholder="Add a skill and press Enter"
          />
          <Button type="button" variant="outline" onClick={addSkill}>
            Add
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {skills.map((skill) => (
            <span
              key={skill}
              className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-1 text-xs"
            >
              {skill}
              <button
                type="button"
                className="text-muted-foreground hover:text-foreground"
                onClick={() =>
                  form.setValue(
                    "skills",
                    skills.filter((item) => item !== skill),
                    { shouldDirty: true },
                  )
                }
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : mode === "create" ? "Create job" : "Save changes"}
        </Button>
      </div>
    </form>
  );
}
