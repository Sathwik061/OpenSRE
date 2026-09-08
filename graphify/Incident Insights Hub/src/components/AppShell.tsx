import { Link, useRouterState } from "@tanstack/react-router";
import {
  Activity,
  Archive,
  FlaskConical,
  LayoutDashboard,
  Moon,
  Radar,
  Settings,
  Sun,
  Workflow,
  Briefcase,
  Blocks,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { StatusDot } from "./StatusDot";
import { useApp } from "@/lib/app-context";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/incidents", label: "Incidents & RCA", icon: Radar },
  { to: "/history", label: "History", icon: Archive },
  { to: "/processes", label: "Processes", icon: Workflow },
  { to: "/projects", label: "Project Passports", icon: Briefcase },
  { to: "/integrations", label: "Integrations", icon: Blocks },
  { to: "/ingest", label: "Ingest Lab", icon: FlaskConical },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const stored = window.localStorage.getItem("opensre_theme");
    const isDark = stored === "dark";
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);
  return (
    <button
      type="button"
      aria-label="Toggle theme"
      onClick={() => {
        const next = !dark;
        setDark(next);
        document.documentElement.classList.toggle("dark", next);
        window.localStorage.setItem("opensre_theme", next ? "dark" : "light");
      }}
      className="rounded-md border border-border p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
    >
      {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </button>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { statuses, history, aiModel } = useApp();

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r bg-sidebar md:flex">
        <div className="flex items-center gap-2.5 border-b px-5 py-4">
          <span className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity className="size-4" />
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold tracking-tight">OpenSRE</p>
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              incident ops
            </p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-0.5 p-3">
          {NAV.map(({ to, label, icon: Icon }) => {
            const active = to === "/" ? pathname === "/" : pathname.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  "group relative flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-all duration-200",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
                )}
              >
                <span
                  className={cn(
                    "absolute left-0 h-5 w-0.5 rounded-full bg-primary transition-all duration-200",
                    active ? "opacity-100" : "opacity-0",
                  )}
                />
                <Icon className="size-4 transition-transform duration-200 group-hover:translate-x-0.5" />
                {label}
                {to === "/history" && history.length > 0 ? (
                  <span className="ml-auto rounded-full bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                    {history.length}
                  </span>
                ) : null}
              </Link>
            );
          })}
        </nav>

        <div className="space-y-2 border-t p-3">
          <p className="px-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            services
          </p>
          {[
            { label: "Camunda", port: ":8080", status: statuses.camunda },
            { label: "Sentinel", port: ":5000", status: statuses.sentinel },
            { label: "DGX AI", port: ":8000", status: statuses.dgx },
          ].map((s) => (
            <div key={s.label} className="flex items-center gap-2 px-1 text-xs">
              <StatusDot status={s.status} />
              <span className="text-muted-foreground">{s.label}</span>
              <span className="ml-auto font-mono text-[10px] text-muted-foreground">{s.port}</span>
            </div>
          ))}
          {aiModel ? (
            <p
              className="truncate px-1 font-mono text-[10px] text-muted-foreground"
              title={aiModel}
            >
              model: {aiModel}
            </p>
          ) : null}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b bg-background/85 px-4 py-2.5 backdrop-blur md:px-6">
          <div className="flex gap-1 overflow-x-auto md:hidden">
            {NAV.map(({ to, label, icon: Icon }) => {
              const active = to === "/" ? pathname === "/" : pathname.startsWith(to);
              return (
                <Link
                  key={to}
                  to={to}
                  aria-label={label}
                  className={cn(
                    "rounded-md p-2",
                    active ? "bg-accent text-accent-foreground" : "text-muted-foreground",
                  )}
                >
                  <Icon className="size-4" />
                </Link>
              );
            })}
          </div>
          <p className="hidden font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground md:block">
            opensre / {pathname === "/" ? "overview" : pathname.replace("/", "")}
          </p>
          <div className="ml-auto flex items-center gap-2">
            <div className="hidden items-center gap-1.5 rounded-md border bg-card px-2.5 py-1.5 sm:flex">
              <StatusDot status={statuses.sentinel} />
              <span className="font-mono text-[11px] text-muted-foreground">sentinel</span>
              <StatusDot status={statuses.camunda} className="ml-2" />
              <span className="font-mono text-[11px] text-muted-foreground">camunda</span>
              <StatusDot status={statuses.dgx} className="ml-2" />
              <span className="font-mono text-[11px] text-muted-foreground">dgx</span>
            </div>
            <ThemeToggle />
          </div>
        </header>

        <main key={pathname} className="animate-fade-up min-w-0 flex-1 px-4 py-6 md:px-6 md:py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
