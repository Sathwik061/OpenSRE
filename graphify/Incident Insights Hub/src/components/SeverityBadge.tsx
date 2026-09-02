import { cn } from "@/lib/utils";
import type { Severity } from "@/lib/types";

const styles: Record<string, string> = {
  critical: "border-critical/30 bg-critical/10 text-critical",
  high: "border-warning/40 bg-warning/15 text-warning-foreground",
  medium: "border-info/30 bg-info/10 text-info",
  low: "border-border bg-muted text-muted-foreground",
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest",
        styles[severity] ?? styles["low"],
        className,
      )}
    >
      {severity}
    </span>
  );
}

export function TypeChip({ value, className }: { value: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center truncate rounded border border-border bg-surface px-1.5 py-0.5 font-mono text-[11px] text-surface-foreground",
        className,
      )}
      title={value}
    >
      {value}
    </span>
  );
}

export function StateChip({ state }: { state: string }) {
  const s = state.toUpperCase();
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest",
        s === "ACTIVE" && "border-critical/30 bg-critical/10 text-critical",
        s === "RESOLVED" && "border-success/30 bg-success/10 text-success",
        s === "SAVED_HISTORY" && "border-border bg-muted text-muted-foreground",
      )}
    >
      {s.replace("_", " ")}
    </span>
  );
}
