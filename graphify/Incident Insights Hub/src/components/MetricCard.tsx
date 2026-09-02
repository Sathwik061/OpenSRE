import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

function useCountUp(target: number, duration = 700) {
  const [value, setValue] = useState(0);
  const raf = useRef<number | null>(null);
  useEffect(() => {
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(Math.round(from + (target - from) * eased));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [target, duration]);
  return value;
}

export function MetricCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "default",
  delay = 0,
}: {
  label: string;
  value: number | string;
  hint?: string;
  icon?: LucideIcon;
  tone?: "default" | "critical" | "success" | "warning";
  delay?: number;
}) {
  const numeric = typeof value === "number";
  const counted = useCountUp(numeric ? value : 0);
  return (
    <div
      className="animate-fade-up group relative overflow-hidden rounded-lg border bg-card p-4 shadow-[var(--shadow-soft)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[var(--shadow-lift)]"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
        {Icon ? (
          <Icon
            className={cn(
              "size-4 transition-transform duration-300 group-hover:scale-110",
              tone === "critical" && "text-critical",
              tone === "success" && "text-success",
              tone === "warning" && "text-warning",
              tone === "default" && "text-primary",
            )}
          />
        ) : null}
      </div>
      <p
        className={cn(
          "mt-3 truncate font-mono tracking-tight",
          numeric ? "text-3xl" : "text-xl",
          tone === "critical" && "text-critical",
          tone === "success" && "text-success",
        )}
      >
        {numeric ? counted : value}
      </p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
      <span className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
    </div>
  );
}
