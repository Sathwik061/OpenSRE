import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  Database,
  Pause,
  Play,
  RefreshCw,
  Radar,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MetricCard } from "@/components/MetricCard";
import { EmptyState } from "@/components/EmptyState";
import { StatusPill } from "@/components/StatusDot";
import { StateChip, TypeChip } from "@/components/SeverityBadge";
import { useApp } from "@/lib/app-context";
import { useCamundaData } from "@/lib/use-incidents";
import { INCIDENT_CASES, caseToRecord } from "@/lib/incident-cases";
import { formatTime, relativeTime } from "@/lib/rca-format";
import { downloadJson, saveHistoryRecord } from "@/lib/storage";
import type { CamundaIncident, HistoryRecord } from "@/lib/types";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Overview — OpenSRE Dashboard" },
      {
        name: "description",
        content:
          "Live overview of Camunda process instances, active workflow incidents, AI engine health and saved RCA investigations.",
      },
      { property: "og:title", content: "Overview — OpenSRE Dashboard" },
      {
        property: "og:description",
        content: "Live metrics for workflow incidents, AI engine health and saved investigations.",
      },
    ],
  }),
  component: DashboardPage,
});

function incidentToRecord(inc: CamundaIncident): HistoryRecord {
  return {
    id: inc.processInstanceKey || inc.incidentKey,
    savedAt: new Date().toISOString(),
    source: "camunda",
    title: `${inc.errorType} · ${inc.processDefinitionId}`,
    service: inc.processDefinitionId,
    environment: "production",
    severity: "high",
    errorType: inc.errorType,
    errorMessage: inc.errorMessage,
    resolutionStatus: inc.state === "RESOLVED" ? "resolved" : "open",
    incidentKey: inc.incidentKey,
    processDefinitionId: inc.processDefinitionId,
    processInstanceKey: inc.processInstanceKey,
    elementId: inc.elementId,
    creationTime: inc.creationTime,
    rca: inc.rca,
    rawOutput: inc.rawOutput,
  };
}

function DashboardPage() {
  const navigate = useNavigate();
  const { history, statuses, aiModel, config, refreshHistory } = useApp();
  const { incidents, instances, error, loading, lastUpdated, paused, setPaused, refresh } =
    useCamundaData();

  const active = incidents.filter((i) => (i.state ?? "ACTIVE").toUpperCase() === "ACTIVE");
  const resolvedLocal = history.filter((h) => h.resolutionStatus === "resolved").length;

  function loadCase(caseId: string) {
    const c = INCIDENT_CASES.find((x) => x.id === caseId);
    if (!c) return;
    const record = caseToRecord(c);
    saveHistoryRecord(record);
    refreshHistory();
    toast.success("Incident case loaded", { description: c.label });
    void navigate({ to: "/incidents", search: { id: record.id } });
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Operations overview</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Real-time workflow incident posture across Camunda, Sentinel RCA and the local
            inference engine.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1.5">
                <Zap className="size-3.5" /> Quick incident case <ChevronDown className="size-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              <DropdownMenuLabel>Predefined scenarios</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {INCIDENT_CASES.map((c) => (
                <DropdownMenuItem key={c.id} onSelect={() => loadCase(c.id)}>
                  <span className="truncate">{c.label}</span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <Button variant="outline" size="sm" onClick={() => setPaused(!paused)} className="gap-1.5">
            {paused ? <Play className="size-3.5" /> : <Pause className="size-3.5" />}
            {paused ? "Resume" : "Pause"}
          </Button>
          <Button size="sm" onClick={() => void refresh()} className="gap-1.5">
            <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
        </div>
      </header>

      {error ? (
        <div className="animate-fade-up flex flex-wrap items-center gap-3 rounded-lg border border-warning/40 bg-warning/10 px-4 py-3 text-sm">
          <AlertTriangle className="size-4 text-warning" />
          <span>
            Camunda at <span className="font-mono">{config.camundaUrl}</span> is unreachable —
            showing locally saved investigations.
          </span>
          <Button variant="outline" size="sm" className="ml-auto" onClick={() => void refresh()}>
            Retry
          </Button>
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Process instances" value={instances.length} icon={Database} delay={0} />
        <MetricCard
          label="Active incidents"
          value={active.length}
          icon={AlertTriangle}
          tone="critical"
          delay={60}
        />
        <MetricCard
          label="Resolved"
          value={resolvedLocal}
          icon={CheckCircle2}
          tone="success"
          delay={120}
        />
        <MetricCard label="History records" value={history.length} icon={Radar} delay={180} />
        <MetricCard
          label="AI engine"
          value={statuses.dgx === "online" ? "Connected" : "Disconnected"}
          hint={aiModel ?? config.dgxUrl}
          icon={BrainCircuit}
          tone={statuses.dgx === "online" ? "success" : "critical"}
          delay={240}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="animate-fade-up overflow-hidden rounded-lg border bg-card">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold tracking-tight">Live incidents</h2>
              <p className="text-xs text-muted-foreground">
                {lastUpdated ? `Updated ${relativeTime(lastUpdated)}` : "Waiting for first poll"} ·
                every {config.pollingIntervalMs / 1000}s
              </p>
            </div>
            <span className="font-mono text-xs text-muted-foreground">{incidents.length} rows</span>
          </div>

          {incidents.length === 0 ? (
            <div className="p-4">
              <EmptyState
                icon={Radar}
                title="No live incidents"
                description="Either Camunda has no active incidents or the engine is offline. Load a predefined case to explore the RCA workflow."
              />
            </div>
          ) : (
            <div className="max-h-[520px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-surface/95 backdrop-blur">
                  <tr className="text-left text-[10px] uppercase tracking-wider text-muted-foreground">
                    <th className="px-4 py-2 font-medium">Instance key</th>
                    <th className="px-4 py-2 font-medium">Process</th>
                    <th className="px-4 py-2 font-medium">Element</th>
                    <th className="px-4 py-2 font-medium">Error type</th>
                    <th className="px-4 py-2 font-medium">Created</th>
                    <th className="px-4 py-2 font-medium">State</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {incidents.map((inc, i) => (
                    <tr
                      key={inc.processInstanceKey || inc.incidentKey}
                      className="animate-fade-up border-t transition-colors hover:bg-accent/40"
                      style={{ animationDelay: `${Math.min(i * 30, 300)}ms` }}
                    >
                      <td className="px-4 py-2 font-mono text-xs">
                        {inc.processInstanceKey || inc.incidentKey}
                      </td>
                      <td className="max-w-40 truncate px-4 py-2 text-xs" title={inc.processDefinitionId}>
                        {inc.processDefinitionId}
                      </td>
                      <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                        {inc.elementId}
                      </td>
                      <td className="px-4 py-2">
                        <TypeChip value={inc.errorType} />
                      </td>
                      <td className="px-4 py-2 text-xs text-muted-foreground">
                        {formatTime(inc.creationTime)}
                      </td>
                      <td className="px-4 py-2">
                        <StateChip state={inc.state ?? "ACTIVE"} />
                      </td>
                      <td className="px-4 py-2 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs">
                              Actions <ChevronDown className="size-3" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onSelect={() => {
                                const rec = incidentToRecord(inc);
                                saveHistoryRecord(rec);
                                refreshHistory();
                                void navigate({ to: "/incidents", search: { id: rec.id } });
                              }}
                            >
                              <Radar className="size-4" /> Open RCA view
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onSelect={() => {
                                saveHistoryRecord(incidentToRecord(inc));
                                refreshHistory();
                                toast.success("Saved to local history");
                              }}
                            >
                              <CheckCircle2 className="size-4" /> Save to history
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onSelect={() => downloadJson(`incident-${inc.incidentKey}.json`, inc)}
                            >
                              <Activity className="size-4" /> Export JSON
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="animate-fade-up space-y-3 rounded-lg border bg-card p-4">
          <h2 className="text-sm font-semibold tracking-tight">System status</h2>
          <StatusPill label="Camunda" status={statuses.camunda} detail=":8080" />
          <StatusPill label="Sentinel" status={statuses.sentinel} detail=":5000" />
          <StatusPill label="DGX AI" status={statuses.dgx} detail=":8000" />
          <div className="grid-paper mt-3 rounded-md border p-3">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
              local storage
            </p>
            <p className="mt-1 font-mono text-2xl">{history.length}</p>
            <p className="text-xs text-muted-foreground">investigations archived offline</p>
          </div>
        </div>
      </div>
    </div>
  );
}
