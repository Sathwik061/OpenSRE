import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo } from "react";
import { AlertTriangle, Layers, Radar, RefreshCw } from "lucide-react";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState } from "@/components/EmptyState";
import { RcaDetail } from "@/components/RcaDetail";
import { OperateBpmnViewer } from "@/components/OperateBpmnViewer";
import { useApp } from "@/lib/app-context";
import { useCamundaData } from "@/lib/use-incidents";
import { relativeTime } from "@/lib/rca-format";
import { camunda } from "@/lib/api";
import { saveHistoryRecord } from "@/lib/storage";
import type { CamundaIncident, HistoryRecord } from "@/lib/types";
import { cn } from "@/lib/utils";

const searchSchema = z.object({ id: z.string().optional() });

export const Route = createFileRoute("/incidents")({
  validateSearch: searchSchema,
  head: () => ({
    meta: [
      { title: "Incidents & Live RCA Stream — OpenSRE" },
      {
        name: "description",
        content:
          "Live Camunda incidents, BPMN process diagram visualization and structured AI root cause analysis.",
      },
      { property: "og:title", content: "Incidents & Live RCA Stream — OpenSRE" },
      {
        property: "og:description",
        content: "Structured AI root cause analysis and live BPMN process visualization for workflow incidents.",
      },
    ],
  }),
  component: IncidentsPage,
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
    resolutionStatus: (inc.state ?? "").toUpperCase() === "RESOLVED" ? "resolved" : "open",
    incidentKey: inc.incidentKey,
    processDefinitionId: inc.processDefinitionId,
    processInstanceKey: inc.processInstanceKey,
    elementId: inc.elementId,
    creationTime: inc.creationTime,
    rca: inc.rca,
    rawOutput: inc.rawOutput,
  };
}

function IncidentsPage() {
  const { id } = Route.useSearch();
  const navigate = useNavigate({ from: "/incidents" });
  const { history, config, refreshHistory } = useApp();
  const { incidents, error, loading, refresh, lastUpdated } = useCamundaData();

  const merged: HistoryRecord[] = useMemo(() => {
    const historyMap = new Map(history.map((h) => [h.id, h]));
    const live = incidents.map((inc) => {
      const baseRec = incidentToRecord(inc);
      const saved = historyMap.get(baseRec.id);
      if (saved) {
        return {
          ...baseRec,
          ...saved,
          rca: baseRec.rca ?? saved.rca,
          rawOutput: baseRec.rawOutput ?? saved.rawOutput,
          notes: saved.notes ?? baseRec.notes,
        };
      }
      return baseRec;
    });
    const liveIds = new Set(live.map((l) => l.id));
    return [...live, ...history.filter((h) => !liveIds.has(h.id))];
  }, [incidents, history]);

  const selected = merged.find((m) => m.id === id) ?? merged[0] ?? null;

  useEffect(() => {
    if (!selected?.processInstanceKey || selected.variables) return;
    let cancelled = false;
    void camunda
      .searchVariables(config.camundaUrl, selected.processInstanceKey)
      .then((vars) => {
        if (cancelled || vars.length === 0) return;
        const map: Record<string, string> = {};
        vars.forEach((v) => (map[v.name] = v.value));
        saveHistoryRecord({ ...selected, variables: map });
        refreshHistory();
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [selected, config.camundaUrl, refreshHistory]);

  function select(recordId: string) {
    void navigate({ search: { id: recordId } });
  }

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Incidents & live RCA stream</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {lastUpdated ? `Camunda synced ${relativeTime(lastUpdated)}` : "Awaiting Camunda"} ·{" "}
            {merged.length} incident{merged.length === 1 ? "" : "s"} in scope
          </p>
        </div>

        <div className="flex items-center gap-2">
          {merged.length > 1 ? (
            <Select value={selected?.id} onValueChange={(val) => select(val)}>
              <SelectTrigger className="w-[340px] text-xs">
                <SelectValue placeholder="Select incident..." />
              </SelectTrigger>
              <SelectContent>
                {merged.map((m) => (
                  <SelectItem key={m.id} value={m.id}>
                    {m.title} ({m.processInstanceKey || m.incidentKey || m.id})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : null}

          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => void refresh()}>
            <RefreshCw className={cn("size-3.5", loading && "animate-spin")} /> Refresh
          </Button>
        </div>
      </header>

      {error ? (
        <div className="flex items-center gap-2 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-xs">
          <AlertTriangle className="size-3.5 text-warning" />
          Camunda offline — browsing saved investigations from local storage.
        </div>
      ) : null}

      {/* UPPER PART: Live Camunda Operate BPMN Process Diagram Visualization */}
      {selected ? (
        <section className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Layers className="size-3.5 text-primary" /> Live Process Diagram Visualization
            </h2>
            <span className="text-[11px] font-mono text-muted-foreground">
              Element: {selected.elementId || "—"}
            </span>
          </div>

          <OperateBpmnViewer
            processDefinitionId={selected.processDefinitionId}
            processInstanceKey={selected.processInstanceKey}
            elementId={selected.elementId}
            errorType={selected.errorType}
            errorMessage={selected.errorMessage}
          />
        </section>
      ) : null}

      {/* BOTTOM PART: Incidents & Live RCA Stream */}
      <div className="w-full">
        {selected ? (
          <RcaDetail
            record={selected}
            onChanged={(r) => select(r.id)}
            onDeleted={() => void navigate({ search: {} })}
          />
        ) : (
          <EmptyState
            icon={Radar}
            title="No active incidents"
            description="All workflows are operating normally. Incidents will appear here automatically when detected in Camunda."
          />
        )}
      </div>
    </div>
  );
}
