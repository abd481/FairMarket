"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { Check, ChevronsUpDown, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLocations } from "@/hooks/use-locations";
import { Skeleton } from "@/components/ui/skeleton";

interface LocationComboboxProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  hasError?: boolean;
}

export function LocationCombobox({
  value,
  onChange,
  disabled,
  hasError,
}: LocationComboboxProps) {
  const t = useTranslations("valuation");
  const { data: locations, isLoading, isError, refetch } = useLocations();

  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [activeIndex, setActiveIndex] = React.useState(-1);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLUListElement>(null);

  const filtered = React.useMemo(() => {
    if (!locations) return [];
    const q = query.trim().toLowerCase();
    if (!q) return locations.slice(0, 200);
    return locations
      .filter((loc) => loc.toLowerCase().includes(q))
      .slice(0, 200);
  }, [locations, query]);

  React.useEffect(() => {
    if (!open) return;
    function handlePointerDown(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [open]);

  function select(location: string) {
    onChange(location);
    setOpen(false);
    setQuery("");
    setActiveIndex(-1);
    inputRef.current?.blur();
  }

  function handleKeyDown(event: React.KeyboardEvent) {
    if (!open && (event.key === "ArrowDown" || event.key === "Enter")) {
      setOpen(true);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      const item = filtered[activeIndex];
      if (item) select(item);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  React.useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const el = listRef.current.children[activeIndex] as HTMLElement | undefined;
      el?.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search
          className="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <input
          ref={inputRef}
          role="combobox"
          aria-expanded={open}
          aria-controls="location-listbox"
          aria-autocomplete="list"
          autoComplete="off"
          value={open ? query : value}
          placeholder={t("placeholders.location")}
          onChange={(e) => {
            setQuery(e.target.value);
            setActiveIndex(-1);
          }}
          onFocus={() => {
            setQuery("");
            setOpen(true);
          }}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          className={cn(
            "flex h-10 w-full items-center rounded-md border border-input bg-card px-3 py-2 ps-9 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            hasError && "border-destructive focus-visible:ring-destructive",
          )}
        />
        <ChevronsUpDown
          className="pointer-events-none absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
      </div>

      {open && (
        <div className="absolute z-50 mt-1 w-full overflow-hidden rounded-md border bg-card shadow-md">
          {isLoading && (
            <div className="space-y-2 p-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          )}
          {isError && (
            <div className="p-3 text-sm text-muted-foreground">
              <button
                type="button"
                onClick={() => refetch()}
                className="font-medium text-primary hover:underline"
              >
                {t("errors.locationRequired")} — {t("apiError")}
              </button>
            </div>
          )}
          {!isLoading && !isError && filtered.length === 0 && (
            <p className="p-3 text-sm text-muted-foreground">
              {t("locationNotFound")}
            </p>
          )}
          {!isLoading && !isError && filtered.length > 0 && (
            <ul
              ref={listRef}
              id="location-listbox"
              role="listbox"
              className="max-h-64 overflow-auto p-1"
            >
              {filtered.map((loc, index) => (
                <li
                  key={loc}
                  role="option"
                  aria-selected={value === loc}
                  onClick={() => select(loc)}
                  onMouseEnter={() => setActiveIndex(index)}
                  className={cn(
                    "flex cursor-pointer items-center justify-between rounded-sm px-3 py-2 text-sm",
                    index === activeIndex
                      ? "bg-secondary text-secondary-foreground"
                      : "text-foreground",
                  )}
                >
                  <span className="truncate">{loc}</span>
                  {value === loc && (
                    <Check className="h-4 w-4 shrink-0 text-accent" aria-hidden="true" />
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}