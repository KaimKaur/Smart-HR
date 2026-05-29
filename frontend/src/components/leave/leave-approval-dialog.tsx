"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useApproveLeave, useRejectLeave } from "@/hooks/use-leave";
import { useToast } from "@/hooks/use-toast";
import type { LeaveRequest } from "@/types/api";

export function LeaveApprovalDialog({
  request,
  onClose,
  onSuccess,
}: {
  request: LeaveRequest;
  onClose: () => void;
  onSuccess?: () => void;
}) {
  const toast = useToast();
  const approveMutation = useApproveLeave();
  const rejectMutation = useRejectLeave();
  const [remarks, setRemarks] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg space-y-4 rounded-xl border bg-background p-6">
        <h2 className="text-lg font-semibold">Review leave request</h2>
        <div className="rounded-lg border p-3 text-sm">
          <p className="font-medium">{request.employee_name}</p>
          <p>
            {request.leave_type_name}: {request.start_date} to {request.end_date}
          </p>
          <p className="mt-1 text-muted-foreground">{request.reason || "No reason provided."}</p>
        </div>
        <label className="grid gap-1 text-sm">
          <span className="font-medium">Remarks</span>
          <textarea
            rows={4}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            placeholder="Optional approval/rejection remarks"
            value={remarks}
            onChange={(event) => setRemarks(event.target.value)}
          />
        </label>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={rejectMutation.isPending || approveMutation.isPending}
            onClick={async () => {
              await rejectMutation.mutateAsync({ leaveRequestId: request.id, remarks: remarks || undefined });
              toast.success("Leave request rejected.");
              onSuccess?.();
              onClose();
            }}
          >
            Reject
          </Button>
          <Button
            type="button"
            disabled={approveMutation.isPending || rejectMutation.isPending}
            onClick={async () => {
              await approveMutation.mutateAsync({ leaveRequestId: request.id, remarks: remarks || undefined });
              toast.success("Leave request approved.");
              onSuccess?.();
              onClose();
            }}
          >
            Approve
          </Button>
        </div>
      </div>
    </div>
  );
}
