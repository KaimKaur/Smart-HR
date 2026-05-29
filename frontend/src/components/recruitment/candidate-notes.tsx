"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormField } from "@/components/common/form-field";
import { Button } from "@/components/ui/button";
import { useCreateCandidateNote, useCandidateNotes } from "@/hooks/use-candidates";
import { createNoteSchema } from "@/lib/validations";

type NoteFormValues = z.infer<typeof createNoteSchema>;

export function CandidateNotes({ candidateId }: { candidateId: string }) {
  const notesQuery = useCandidateNotes(candidateId);
  const createNote = useCreateCandidateNote(candidateId);

  const form = useForm<NoteFormValues>({
    resolver: zodResolver(createNoteSchema),
    defaultValues: { note: "" },
  });

  return (
    <div className="space-y-4">
      <form
        className="space-y-3"
        onSubmit={form.handleSubmit(async (values) => {
          await createNote.mutateAsync(values.note);
          form.reset();
        })}
      >
        <FormField label="Add note" required error={form.formState.errors.note?.message}>
          <textarea rows={3} className="w-full rounded-lg border px-3 py-2 text-sm" {...form.register("note")} />
        </FormField>
        <Button type="submit" disabled={createNote.isPending}>
          {createNote.isPending ? "Saving..." : "Add note"}
        </Button>
      </form>

      <ul className="space-y-3">
        {(notesQuery.data ?? []).map((note) => (
          <li key={note.id} className="rounded-lg border bg-card p-3">
            <p className="text-sm">{note.note}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              {note.created_by_name ?? "Recruiter"} · {new Date(note.created_at).toLocaleString()}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
