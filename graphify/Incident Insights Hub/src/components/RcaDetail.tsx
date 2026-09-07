import { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ClipboardCopy,
  Copy,
  Database,
  Download,
  ExternalLink,
  ListChecks,
  Loader2,
  Quote,
  Save,
  Search,
  Sparkles,
  Terminal,
  TriangleAlert,
  Trash2,
  Wrench,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Textarea } from "@/components/ui/textarea";
import { SeverityBadge, TypeChip } from "./SeverityBadge";
import { camunda, pollInvestigation, sentinel } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import { caseToPayload } from "@/lib/incident-cases";
import { formatTime, recordToMarkdown } from "@/lib/rca-format";
import {
  deleteHistoryRecords,
  downloadJson,
  saveHistoryRecord,
  updateHistoryRecord,
} from "@/lib/storage";
import { maskVariables, maskStringValue } from "@/lib/masking";
import type { HistoryRecord, IncidentCase } from "@/lib/types";

function Section({
  title,
  icon: Icon,
  children,
  accent,
  badge,
}: {
  title: string;
  icon: typeof AlertTriangle;
  children: React.ReactNode;
  accent?: string;
  badge?: React.ReactNode;
}) {
  return (
    <section className="animate-fade-up rounded-lg border border-border bg-card p-4 shadow-sm transition-all hover:border-slate-300 dark:hover:border-slate-700">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`size-4 ${accent ?? "text-primary"}`} />
          <h3 className="text-sm font-semibold tracking-tight text-foreground">{title}</h3>
        </div>
        {badge}
      </div>
      <div className="text-sm leading-relaxed text-foreground/90">{children}</div>
    </section>
  );
}

export function RcaDetail({
  record,
  onChanged,
  onDeleted,
}: {
  record: HistoryRecord;
  onChanged?: (r: HistoryRecord) => void;
  onDeleted?: (id: string) => void;
}) {
  const { config, refreshHistory } = useApp();
  const [notes, setNotes] = useState(record.notes ?? "");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);

  useEffect(() => {
    setNotes(record.notes ?? "");
  }, [record.id, record.notes]);

  // Continuously ensure authoritative DGX RCA is loaded from Sentinel/Supabase
  useEffect(() => {
    const lookupKey = (record.processInstanceKey || record.incidentKey || record.id) as string;
    if (!lookupKey) return;

    sentinel
      .getInvestigation(config.sentinelUrl, lookupKey)
      .then((res) => {
        if (res?.rca && res.rca.summary) {
          // If the fetched RCA is different or richer than the current one, update it!
          if (
            !record.rca ||
            record.rca.summary !== res.rca.summary ||
            (res.rca.recommended_actions?.length ?? 0) > (record.rca.recommended_actions?.length ?? 0)
          ) {
            const updated: HistoryRecord = {
              ...record,
              rca: res.rca,
              rawOutput: res.raw_output ?? "",
            };
            saveHistoryRecord(updated);
            refreshHistory();
            onChanged?.(updated);
          }
        }
      })
      .catch(() => {});
  }, [
    record.id,
    record.processInstanceKey,
    record.incidentKey,
    record.rca?.summary,
    config.sentinelUrl,
  ]);

  useEffect(() => {
    const t = window.setTimeout(() => {
      if ((record.notes ?? "") !== notes) {
        updateHistoryRecord(record.id, { notes });
        refreshHistory();
      }
    }, 600);
    return () => window.clearTimeout(t);
  }, [notes, record.id, record.notes, refreshHistory]);

  const rca = record.rca;

  async function runAnalysis() {
    setRunning(true);
    setProgress("Dispatching to Sentinel & DGX Qwen 35B…");
    try {
      const payload =
        record.payload ??
        caseToPayload({
          id: record.id,
          label: record.title,
          category: "adhoc",
          service: record.service,
          environment: record.environment,
          severity: record.severity,
          errorType: record.errorType,
          errorMessage: record.errorMessage,
          elementId: record.elementId ?? "",
          processDefinitionId: record.processDefinitionId ?? "",
          logs: [record.errorMessage],
          timeline: [],
          variables: record.variables ?? {},
        } as IncidentCase);
      const accepted = await sentinel.investigate(config.sentinelUrl, payload);
      setProgress("Investigation accepted, querying DGX Qwen 35B…");
      const result = await pollInvestigation(config.sentinelUrl, accepted.investigation_id, (n) =>
        setProgress(`Analyzing incident… attempt ${n}`),
      );
      const rcaVersion = result.camunda_version || result.rca?.camunda_version || record.camunda_version || record.payload?.camunda_version || payload.camunda_version;
      const enhancedRca = result.rca
        ? {
            ...result.rca,
            camunda_version: rcaVersion,
            documentation_references: (result.rca.documentation_references || []).map((d) => ({
              ...d,
              camunda_version: d.camunda_version || rcaVersion,
            })),
          }
        : undefined;

      const updated: HistoryRecord = {
        ...record,
        camunda_version: rcaVersion,
        payload: {
          ...payload,
          camunda_version: rcaVersion,
        },
        rca: enhancedRca,
        rawOutput: result.raw_output ?? "",
        resolutionStatus: "investigating",
        savedAt: new Date().toISOString(),
      };
      saveHistoryRecord(updated);
      refreshHistory();
      onChanged?.(updated);
      toast.success("DGX AI analysis complete", { description: record.title });
    } catch (e) {
      toast.error("Sentinel investigation failed", {
        description: e instanceof Error ? e.message : "Service unreachable at " + config.sentinelUrl,
      });
    } finally {
      setRunning(false);
      setProgress(null);
    }
  }

  async function resolveInCamunda() {
    if (!record.incidentKey) {
      toast.error("No Camunda incident key on this record");
      return;
    }
    try {
      await camunda.resolveIncident(config.camundaUrl, record.incidentKey);
      const updated = { ...record, resolutionStatus: "resolved" as const };
      saveHistoryRecord(updated);
      refreshHistory();
      onChanged?.(updated);
      toast.success("Incident resolution requested in Camunda");
    } catch (e) {
      toast.error("Could not resolve incident", {
        description: e instanceof Error ? e.message : "Camunda unreachable",
      });
    }
  }

  async function saveToRunbookStore() {
    if (!record.rca) {
      toast.error("No RCA analysis available to save as runbook");
      return;
    }
    try {
      await sentinel.saveRunbook(config.sentinelUrl, {
        error_type: record.errorType,
        service: record.service || record.processDefinitionId || "*",
        title: `${record.errorType} SOP Playbook`,
        rca: record.rca,
        confidence: record.rca.confidence || "HIGH",
      });
      toast.success("Successfully persisted to SRE Runbook Knowledge Store", {
        description: `Saved canonical SOP for ${record.errorType}`,
      });
    } catch (e) {
      toast.error("Failed to save runbook", {
        description: e instanceof Error ? e.message : "Sentinel connection error",
      });
    }
  }

  function copyMarkdown() {
    const md = recordToMarkdown(record);
    void navigator.clipboard.writeText(md);
    toast.success("Copied full RCA markdown to clipboard");
  }

  return (
    <div className="space-y-4">
      {/* Top Header Card */}
      <div className="rounded-lg border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <SeverityBadge severity={record.severity} />
              <TypeChip type={record.errorType} />
              {(record.rca?.camunda_version || record.camunda_version || record.payload?.camunda_version) ? (
                <span className="inline-flex items-center rounded-full border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 font-mono text-[10px] font-semibold text-blue-600 dark:text-blue-400">
                  Camunda {record.rca?.camunda_version || record.camunda_version || record.payload?.camunda_version}
                </span>
              ) : null}
              <span className="text-xs text-muted-foreground font-mono">{record.environment}</span>
            </div>
            <h2 className="text-lg font-bold tracking-tight text-foreground">{record.title}</h2>
            <p className="text-xs text-muted-foreground font-mono max-w-3xl leading-relaxed">
              {maskStringValue(record.errorMessage || record.rca?.summary || "No explicit error message recorded.")}
            </p>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm" variant="outline" className="gap-1.5 font-medium">
                Actions <ChevronDown className="size-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 text-xs">
              <DropdownMenuLabel>Incident Operations</DropdownMenuLabel>
              <DropdownMenuItem onSelect={() => void runAnalysis()} disabled={running}>
                <BrainCircuit className="size-4" /> Run AI Investigation
              </DropdownMenuItem>
              <DropdownMenuItem
                onSelect={() => void resolveInCamunda()}
                disabled={!record.incidentKey}
              >
                <CheckCircle2 className="size-4 text-emerald-600" /> Resolve in Camunda
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => void saveToRunbookStore()}>
                <BookOpen className="size-4 text-blue-600" /> Save as SRE Runbook
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={copyMarkdown}>
                <Copy className="size-4" /> Copy RCA as Markdown
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => downloadJson(record, `${record.id}-rca.json`)}>
                <Download className="size-4" /> Download JSON
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onSelect={() => {
                  deleteHistoryRecords([record.id]);
                  refreshHistory();
                  onDeleted?.(record.id);
                  toast.success("Deleted from history");
                }}
              >
                <Trash2 className="size-4" /> Delete from History
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Process Metadata Grid */}
        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 border-t pt-3 text-xs lg:grid-cols-4">
          {[
            ["Process definition", record.processDefinitionId],
            ["Instance key", record.processInstanceKey],
            ["Element ID", record.elementId],
            ["Created", formatTime(record.creationTime ?? record.savedAt)],
            ["Incident key", record.incidentKey],
            ["Service", record.service],
            ["Status", record.resolutionStatus],
            ["Confidence", rca?.confidence || "HIGH"],
          ].map(([label, value]) => (
            <div key={label as string} className="min-w-0">
              <dt className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
                {label}
              </dt>
              <dd className="truncate font-mono text-xs text-foreground font-medium" title={String(value ?? "—")}>
                {value || "—"}
              </dd>
            </div>
          ))}
        </dl>

        {running ? (
          <div className="mt-3 overflow-hidden rounded-md border bg-muted/40 px-3 py-2">
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin text-primary" /> {progress}
            </p>
            <div className="mt-2 h-0.5 w-full overflow-hidden rounded bg-border">
              <div className="animate-sweep h-full w-1/3 bg-primary" />
            </div>
          </div>
        ) : null}
      </div>


      {/* Process Variables at Failure */}
      {record.variables && Object.keys(record.variables).length > 0 ? (
        <Section title="📦 Process Variables at Failure" icon={ListChecks}>
          <div className="overflow-hidden rounded-md border bg-card">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b bg-muted/40 text-[11px] text-muted-foreground">
                  <th className="px-3 py-1.5 text-left font-semibold">Variable Name</th>
                  <th className="px-3 py-1.5 text-left font-semibold">Value at Incident Execution</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(maskVariables(record.variables)).map(([k, v], i) => (
                  <tr key={k} className={i % 2 ? "bg-muted/20" : ""}>
                    <td className="w-1/3 border-r px-3 py-1.5 font-mono font-medium text-foreground">
                      {k}
                    </td>
                    <td className="px-3 py-1.5 font-mono break-all text-foreground">
                      {v === null || v === "null" || v === undefined ? (
                        <span className="text-muted-foreground italic">null</span>
                      ) : (
                        String(v)
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      ) : null}

      {/* Structured Elaborate RCA Content */}
      {rca ? (
        <>
          {/* WHAT is the error? */}
          <Section title="❓ WHAT is the error?" icon={AlertTriangle} accent="text-rose-600">
            <p className="font-medium text-foreground leading-relaxed">{maskStringValue(rca.summary)}</p>
          </Section>

          {/* WHY did it occur? (Root Cause) */}
          <Section title="🔍 WHY did it occur? (Root Cause)" icon={Search} accent="text-amber-600">
            <div className="rounded-md bg-muted/30 border border-border/60 p-3.5 leading-relaxed text-foreground font-normal">
              {maskStringValue(rca.root_cause)}
            </div>
          </Section>

          {/* BPMN Topology Warnings (Parallel Deadlock, Missing Boundary, etc.) */}
          {rca.topology_warnings && rca.topology_warnings.length > 0 ? (
            <Section title="⚠️ BPMN Topology Warnings" icon={TriangleAlert} accent="text-orange-600">
              <div className="space-y-2">
                {rca.topology_warnings.map((w, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 rounded-md border border-orange-200 bg-orange-50 p-3 dark:border-orange-900/50 dark:bg-orange-950/30"
                  >
                    <TriangleAlert className="mt-0.5 size-4 shrink-0 text-orange-600 dark:text-orange-400" />
                    <p className="text-sm leading-relaxed text-orange-800 font-medium dark:text-orange-300">
                      {maskStringValue(w)}
                    </p>
                  </div>
                ))}
                <p className="text-xs text-muted-foreground mt-1">
                  These warnings are detected by static BPMN topology analysis and may require additional BPMN model changes beyond the incident fix.
                </p>
              </div>
            </Section>
          ) : null}

          <Section title="📋 Observed Facts" icon={ListChecks}>
            <ul className="space-y-2">
              {rca.observed_facts?.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-foreground">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                  <span className="leading-relaxed">
                    {/* Render variable lines with monospace styling */}
                    {f.startsWith("Variable ") ? (
                      <code>{maskStringValue(f)}</code>
                    ) : (
                      maskStringValue(f)
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </Section>

          {/* Cited Evidence */}
          {(() => {
            const evidenceList =
              rca.evidence && rca.evidence.length > 0
                ? rca.evidence
                : record.errorMessage
                  ? [record.errorMessage]
                  : [];
            if (evidenceList.length === 0) return null;
            return (
              <Section title="💬 Cited Evidence" icon={Quote}>
                <div className="space-y-2">
                  {evidenceList.map((e, i) => (
                    <pre
                      key={i}
                      className="overflow-x-auto rounded-md border bg-muted/40 p-3 font-mono text-xs text-foreground whitespace-pre-wrap leading-relaxed"
                    >
                      {maskStringValue(e)}
                    </pre>
                  ))}
                </div>
              </Section>
            );
          })()}

          {/* HOW to fix it? */}
          <Section title="🛠️ HOW to fix it?" icon={Wrench} accent="text-emerald-600">
            <ol className="space-y-2.5">
              {rca.recommended_actions?.map((a, i) => (
                <li key={i} className="flex items-start gap-3 rounded-md border border-border/60 bg-muted/20 p-2.5 text-foreground">
                  <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary font-mono text-[11px] font-bold text-primary-foreground">
                    {i + 1}
                  </span>
                  <span className="leading-relaxed font-medium">{maskStringValue(a)}</span>
                </li>
              ))}
            </ol>
          </Section>

          {/* Official Camunda Documentation References */}
          {rca.documentation_references && rca.documentation_references.length > 0 ? (
            <Section
              title={`📚 Camunda ${rca.camunda_version || record.camunda_version || record.payload?.camunda_version || "8.9"} Documentation & Rules`}
              icon={BookOpen}
              accent="text-blue-600"
            >
              <div className="space-y-2.5">
                {rca.documentation_references.map((doc, i) => {
                  const docVer =
                    doc.camunda_version ||
                    rca.camunda_version ||
                    record.camunda_version ||
                    record.payload?.camunda_version ||
                    "8.9";
                  return (
                    <div
                      key={i}
                      className="flex flex-col gap-1 rounded-md border border-blue-200/70 bg-blue-50/50 p-3 text-xs dark:border-blue-900/50 dark:bg-blue-950/20"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-blue-900 dark:text-blue-300">
                            {doc.section || doc.title || "Camunda Documentation"}
                          </span>
                          <span className="rounded bg-blue-100 px-1.5 py-0.5 font-mono text-[9px] font-bold text-blue-800 dark:bg-blue-900/60 dark:text-blue-300">
                            v{docVer}
                          </span>
                        </div>
                        {doc.url ? (
                          <a
                            href={doc.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 font-mono text-[11px] font-medium text-blue-600 hover:underline dark:text-blue-400"
                          >
                            View Official Doc <ExternalLink className="size-3" />
                          </a>
                        ) : null}
                      </div>
                      {doc.relevance ? (
                        <p className="text-muted-foreground leading-relaxed">
                          {doc.relevance}
                        </p>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </Section>
          ) : null}
        </>
      ) : (
        <Section title="No RCA generated yet" icon={BrainCircuit}>
          <p className="text-muted-foreground">
            Run an AI investigation to generate the structured root cause analysis for this
            incident.
          </p>
          <Button
            size="sm"
            className="mt-3 gap-1.5"
            disabled={running}
            onClick={() => void runAnalysis()}
          >
            {running ? <Loader2 className="size-3.5 animate-spin" /> : <BrainCircuit className="size-3.5" />}
            Run AI Analysis
          </Button>
        </Section>
      )}

      {/* Notes & Annotations */}
      <Section title="📝 Notes & Annotations" icon={ClipboardCopy}>
        <Textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Remediation notes, handover context, ticket links… saved automatically to local storage."
          className="min-h-24 font-mono text-xs"
        />
        <p className="mt-1.5 text-[11px] text-muted-foreground">Autosaved to local storage.</p>
      </Section>
    </div>
  );
}
