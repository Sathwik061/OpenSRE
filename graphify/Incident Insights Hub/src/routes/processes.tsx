import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { AlertTriangle, RefreshCw, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/EmptyState";
import { StateChip, TypeChip } from "@/components/SeverityBadge";
import { useCamundaData } from "@/lib/use-incidents";
import { formatTime } from "@/lib/rca-format";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/processes")({
  head: () => ({
    meta: [
      { title: "Process & Workflow Topology — OpenSRE" },
      {
        name: "description",
        content:
          "Deployed BPMN processes and DMN decisions from Camunda 8.9 with versions, running instances and incident counts.",
      },
      { property: "og:title", content: "Process & Workflow Topology — OpenSRE" },
      {
        property: "og:description",
        content: "Deployed workflow definitions with live instance and incident counts.",
      },
    ],
  }),
  component: ProcessesPage,
});

function ProcessesPage() {
  const { definitions, instances, incidents, error, loading, refresh } = useCamundaData();
  const [query, setQuery] = useState("");
  const [openKey, setOpenKey] = useState<string | null>(null);

  const rows = useMemo(
    () =>
      definitions
        .filter(
          (d) =>
            !query ||
            `${d.name} ${d.processDefinitionId} ${d.processDefinitionKey}`
              .toLowerCase()
              .includes(query.toLowerCase()),
        )
        .map((d) => ({
          ...d,
          activeInstances: instances.filter(
            (i) => i.processDefinitionId === d.processDefinitionId && i.state !== "COMPLETED",
          ),
          relatedIncidents: incidents.filter(
            (i) => i.processDefinitionId === d.processDefinitionId,
          ),
        })),
    [definitions, instances, incidents, query],
  );

  const detail = rows.find((r) => r.processDefinitionKey === openKey);

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Process & workflow topology</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Deployed BPMN and DMN definitions from the Camunda 8.9 engine.
          </p>
        </div>
        <div className="flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter definitions…"
            className="w-56"
          />
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => void refresh()}>
            <RefreshCw className={cn("size-3.5", loading && "animate-spin")} /> Refresh
          </Button>
        </div>
      </header>

      {error ? (
        <div className="flex items-center gap-2 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-xs">
          <AlertTriangle className="size-3.5 text-warning" /> Camunda REST API unreachable — no
          definitions available.
        </div>
      ) : null}

      {rows.length === 0 ? (
        <EmptyState
          icon={Workflow}
          title="No process definitions"
          description="Connect the Camunda engine on :8080 to list deployed BPMN processes and DMN decisions."
        />
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {rows.map((r, i) => (
            <button
              key={r.processDefinitionKey}
              onClick={() => setOpenKey(r.processDefinitionKey)}
              className="animate-fade-up group rounded-lg border bg-card p-4 text-left transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[var(--shadow-lift)]"
              style={{ animationDelay: `${Math.min(i * 40, 320)}ms` }}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="truncate text-sm font-semibold">{r.name || r.processDefinitionId}</p>
                <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                  v{r.version}
                </span>
              </div>
              <p className="mt-1 truncate font-mono text-[11px] text-muted-foreground">
                {r.processDefinitionId}
              </p>
              <div className="mt-3 grid grid-cols-3 gap-2 border-t pt-3 text-center">
                <div>
                  <p className="font-mono text-lg">{r.activeInstances.length}</p>
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                    instances
                  </p>
                </div>
                <div>
                  <p
                    className={cn(
                      "font-mono text-lg",
                      r.relatedIncidents.length > 0 && "text-critical",
                    )}
                  >
                    {r.relatedIncidents.length}
                  </p>
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                    incidents
                  </p>
                </div>
                <div>
                  <p className="truncate font-mono text-lg">{r.processDefinitionKey.slice(-4)}</p>
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">key</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      <Dialog open={!!detail} onOpenChange={(o) => !o && setOpenKey(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{detail?.name || detail?.processDefinitionId}</DialogTitle>
            <DialogDescription className="font-mono text-xs">
              {detail?.processDefinitionId} · v{detail?.version} · key{" "}
              {detail?.processDefinitionKey}
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[60vh] space-y-4 overflow-auto">
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Running instances
              </p>
              {detail?.activeInstances.length ? (
                <div className="space-y-1">
                  {detail.activeInstances.map((inst) => (
                    <div
                      key={inst.processInstanceKey}
                      className="flex items-center gap-2 rounded border bg-surface px-2.5 py-1.5 text-xs"
                    >
                      <span className="font-mono">{inst.processInstanceKey}</span>
                      <StateChip state={inst.state ?? "ACTIVE"} />
                      {inst.hasIncident ? (
                        <span className="ml-auto font-mono text-[10px] text-critical">
                          has incident
                        </span>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No running instances.</p>
              )}
            </div>
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Linked incidents
              </p>
              {detail?.relatedIncidents.length ? (
                <div className="space-y-1">
                  {detail.relatedIncidents.map((inc) => (
                    <div key={inc.incidentKey} className="rounded border bg-surface px-2.5 py-1.5">
                      <div className="flex items-center gap-2">
                        <TypeChip value={inc.errorType} />
                        <span className="font-mono text-[10px] text-muted-foreground">
                          {inc.elementId}
                        </span>
                        <span className="ml-auto text-[10px] text-muted-foreground">
                          {formatTime(inc.creationTime)}
                        </span>
                      </div>
                      <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                        {inc.errorMessage}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No incidents for this definition.</p>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
