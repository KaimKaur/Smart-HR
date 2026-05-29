"use client";

import { useEffect, useState } from "react";

import { searchEmployees } from "@/services/employee.service";
import type { EmployeeSearchItem } from "@/types/api";
import { cn } from "@/lib/utils";

export function EmployeeSearch({
  value,
  onChange,
  placeholder = "Search employee by name or code...",
  disabled,
}: {
  value: string | null;
  onChange: (employeeId: string | null, employee?: EmployeeSearchItem) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<EmployeeSearchItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedLabel, setSelectedLabel] = useState("");

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = window.setTimeout(() => {
      void searchEmployees(query.trim())
        .then((items) => {
          setResults(items);
          setIsOpen(true);
        })
        .catch(() => setResults([]));
    }, 300);

    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    if (!value) {
      setSelectedLabel("");
      return;
    }
    const match = results.find((item) => item.id === value);
    if (match) {
      setSelectedLabel(`${match.full_name} (${match.employee_code})`);
    }
  }, [value, results]);

  return (
    <div className="relative">
      <input
        type="text"
        disabled={disabled}
        placeholder={selectedLabel || placeholder}
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          if (!event.target.value) onChange(null);
        }}
        onFocus={() => {
          if (results.length) setIsOpen(true);
        }}
        className="h-9 w-full rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
      />
      {isOpen && results.length > 0 ? (
        <ul
          className="absolute z-50 mt-1 max-h-56 w-full overflow-auto rounded-lg border bg-popover p-1 shadow-md"
          role="listbox"
        >
          {results.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                role="option"
                className={cn(
                  "w-full rounded-md px-2 py-2 text-left text-sm hover:bg-muted",
                  value === item.id && "bg-muted",
                )}
                onClick={() => {
                  onChange(item.id, item);
                  setSelectedLabel(`${item.full_name} (${item.employee_code})`);
                  setQuery("");
                  setIsOpen(false);
                }}
              >
                <span className="font-medium">{item.full_name}</span>
                <span className="mt-0.5 block text-xs text-muted-foreground">
                  {item.employee_code} · {item.department.name}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
