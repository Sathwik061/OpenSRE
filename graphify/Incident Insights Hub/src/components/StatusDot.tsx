import { cn } from "@/lib/utils";
import type { ServiceStatus } from "@/lib/types";

export function StatusDot({ status, className }: { status: ServiceStatus; className?: string }) {
  return (
    <span
      className={cn(
        "inline-block size-2 rounded-full",
        status === "online" && "bg-success text-success/40 animate-status-pulse",
        status === "offline" && "bg-critical",
        status === "checking" && "bg-warning animate-pulse",
        className,
      )}
      aria-hidden
    />
  );
}

export function StatusPill({
  label,
  status,
  detail,
}: {
  label: string;
  status: ServiceStatus;
  detail?: string;
}) {
  return (
    <div className="flex items-center gap-2 rounded-md border bg-card/60 px-2.5 py-1.5 text-xs">
      <StatusDot status={status} />
      <span className="font-medium">{label}</span>
      {detail ? <span className="font-mono text-[11px] text-muted-foreground">{detail}</span> : null}
      <span
        className={cn(
          "ml-auto font-mono text-[10px] uppercase tracking-wider",
          status === "online" && "text-success",
          status === "offline" && "text-critical",
          status === "checking" && "text-warning",
        )}
      >
        {status === "online" ? "up" : status === "offline" ? "down" : "…"}
      </span>
    </div>
  );
}
