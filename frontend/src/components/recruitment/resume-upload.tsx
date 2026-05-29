"use client";

import { useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { uploadResume } from "@/services/candidate.service";

const ALLOWED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const MAX_BYTES = 10 * 1024 * 1024;

export function ResumeUpload({
  candidateId,
  onUploaded,
  onAnalyze,
}: {
  candidateId: string;
  onUploaded?: () => void;
  onAnalyze?: () => void;
}) {
  const toast = useToast();
  const [progress, setProgress] = useState<number | null>(null);
  const [uploaded, setUploaded] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      if (!ALLOWED_TYPES.includes(file.type)) {
        toast.error("Only PDF and DOCX files are allowed.");
        return;
      }
      if (file.size > MAX_BYTES) {
        toast.error("File must be 10MB or smaller.");
        return;
      }

      setProgress(0);
      try {
        await uploadResume(candidateId, file, setProgress);
        setUploaded(true);
        toast.success("Resume uploaded.");
        onUploaded?.();
      } catch {
        toast.error("Upload failed.");
      } finally {
        setProgress(null);
      }
    },
    [candidateId, onUploaded, toast],
  );

  return (
    <div className="space-y-3">
      <div
        className={`rounded-xl border border-dashed p-6 text-center ${
          isDragging ? "border-primary bg-primary/5" : "border-border"
        }`}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          const file = event.dataTransfer.files[0];
          if (file) void handleFile(file);
        }}
      >
        <p className="text-sm text-muted-foreground">
          Drag and drop a resume here, or choose a file (PDF/DOCX, max 10MB)
        </p>
        <input
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="mt-3 block w-full text-sm"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void handleFile(file);
          }}
        />
      </div>

      {progress !== null ? (
        <div className="space-y-1">
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
          </div>
          <p className="text-xs text-muted-foreground">Uploading... {progress}%</p>
        </div>
      ) : null}

      {uploaded ? (
        <Button type="button" onClick={onAnalyze}>
          Run AI Screening
        </Button>
      ) : null}
    </div>
  );
}
