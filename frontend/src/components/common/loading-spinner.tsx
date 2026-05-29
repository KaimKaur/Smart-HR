export function LoadingSpinner({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-muted-foreground">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
      <span>{label}</span>
    </div>
  );
}
