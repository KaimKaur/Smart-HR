import { cn } from "@/lib/utils";

const statusTone: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  inactive: "bg-gray-100 text-gray-700",
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  draft: "bg-gray-100 text-gray-700",
  published: "bg-green-100 text-green-800",
  closed: "bg-red-100 text-red-800",
  scheduled: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-gray-100 text-gray-700",
  shortlisted: "bg-green-100 text-green-800",
  applied: "bg-blue-100 text-blue-800",
  screening: "bg-yellow-100 text-yellow-800",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        statusTone[status.toLowerCase()] ?? "bg-blue-100 text-blue-800",
      )}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}
