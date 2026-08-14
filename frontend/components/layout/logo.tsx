import { Building2 } from "lucide-react";
import { Link } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function Logo({
  className,
  linkClassName,
}: {
  className?: string;
  linkClassName?: string;
}) {
  return (
    <Link
      href="/"
      className={cn(
        "flex items-center gap-2 text-lg font-semibold tracking-tight text-primary",
        linkClassName,
      )}
    >
      <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Building2 className="h-5 w-5" aria-hidden="true" />
      </span>
      <span className={cn("hidden sm:inline", className)}>FairMarket</span>
    </Link>
  );
}