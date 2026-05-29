import { EmptyState } from "@/components/common/empty-state";
import { LoadingSpinner } from "@/components/common/loading-spinner";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
}

export function DataTable<T>({
  columns,
  rows,
  isLoading,
  emptyTitle = "No data",
  emptyDescription = "There is nothing to display right now.",
  getRowKey,
  onRowClick,
}: {
  columns: DataTableColumn<T>[];
  rows: T[];
  isLoading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  getRowKey?: (row: T, index: number) => string | number;
  onRowClick?: (row: T) => void;
}) {
  if (isLoading) {
    return <LoadingSpinner label="Loading table data..." />;
  }

  if (!rows.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="min-w-full text-sm">
        <thead className="bg-muted/40 text-left">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-3 font-medium">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr
              key={getRowKey ? getRowKey(row, rowIndex) : rowIndex}
              className={onRowClick ? "cursor-pointer border-t hover:bg-muted/40" : "border-t"}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map((column) => (
                <td key={column.key} className="px-4 py-3">
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
