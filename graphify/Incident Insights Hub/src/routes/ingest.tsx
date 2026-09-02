import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { BrainCircuit, FlaskConical, Loader2, Plus, Save, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useApp } from "@/lib/app-context";
import { pollInvestigation, sentinel } from "@/lib/api";
import { INCIDENT_CASES, newId } from "@/lib/incident-cases";
import { getTemplates, saveHistoryRecord, saveTemplate } from "@/lib/storage";
import type { Environment, HistoryRecord, IncidentCase, Severity } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/ingest")({
  head: () => ({
    meta: [
      { title: "Incident & Log Injection Lab — OpenSRE" },
      {
        name: "description",
        content:
          "Manually submit logs, timelines and error payloads to the Sentinel RCA engine and archive the AI investigation locally.",
      },
      { property: "og:title", content: "Incident & Log Injection Lab — OpenSRE" },
      {
        property: "og:description",
        content: "Inject logs and trigger AI root cause investigations on demand.",
      },
    ],
  }),
  component: IngestPage,
});

interface TimelineItem {
  time: string;
  event: string;
}

function IngestPage() {
  const navigate = useNavigate();
  const { config, refreshHistory } = useApp();
  const fileRef = useRef<HTMLInputElement>(null);

  const [service, setService] = useState("");
  const [environment, setEnvironment] = useState<Environment>("production");
  const [severity, setSeverity] = useState<Severity>("high");
  const [errorType, setErrorType] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [logs, setLogs] = useState("");
  const [timeline, setTimeline] = useState<TimelineItem[]>([{ time: "", event: "" }]);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [customTemplates, setCustomTemplates] = useState<IncidentCase[]>(() => getTemplates());

  function applyCase(id: string) {
    if (id === "custom_blank") {
      setService("");
      setErrorType("");
      setErrorMessage("");
      setLogs("");
      setTimeline([{ time: "", event: "" }]);
      toast.info("Custom blank form ready — enter any service or error");
      return;
    }
    const allCases = [...INCIDENT_CASES, ...customTemplates];
    const c = allCases.find((x) => x.id === id);
    if (!c) return;
    setService(c.service);
    setEnvironment(c.environment);
    setSeverity(c.severity);
    setErrorType(c.errorType);
    setErrorMessage(c.errorMessage);
    setLogs(c.logs.join("\n"));
    setTimeline(
      c.timeline.map((t) => {
        const [time, ...rest] = t.split(" — ");
        return { time: time ?? "", event: rest.join(" — ") };
      }),
    );
    toast.success("Case loaded", { description: c.label });
  }

  async function handleFile(file: File) {
    try {
      const parsed = JSON.parse(await file.text()) as Record<string, unknown>;
      setService(String(parsed["service"] ?? parsed["alert_name"] ?? ""));
      setErrorType(String(parsed["error"] ?? parsed["error_type"] ?? ""));
      setErrorMessage(String(parsed["error_message"] ?? ""));
      if (Array.isArray(parsed["logs"])) setLogs((parsed["logs"] as string[]).join("\n"));
      if (Array.isArray(parsed["timeline"]))
        setTimeline(
          (parsed["timeline"] as string[]).map((t) => {
            const [time, ...rest] = String(t).split(" — ");
            return { time: time ?? "", event: rest.join(" — ") };
          }),
        );
      toast.success("Alert file loaded", { description: file.name });
    } catch {
      toast.error("Could not parse JSON file");
    }
  }

  async function trigger() {
    if (!service || !errorType) {
      toast.error("Service name and error type are required");
      return;
    }
    const payload = {
      alert_name: `${errorType} in ${service}`,
      service,
      environment,
      error: errorType,
      error_message: errorMessage,
      logs: logs.split("\n").filter(Boolean),
      timeline: timeline.filter((t) => t.event).map((t) => `${t.time} — ${t.event}`),
      severity,
      request: `Investigate ${errorType} in ${service} (${environment})`,
    };

    const record: HistoryRecord = {
      id: newId("ingest"),
      savedAt: new Date().toISOString(),
      source: "ingest",
      title: payload.alert_name,
      service,
      environment,
      severity,
      errorType,
      errorMessage,
      resolutionStatus: "investigating",
      creationTime: new Date().toISOString(),
      payload,
    };

    setRunning(true);
    setProgress("Dispatching payload to Sentinel…");
    try {
      const accepted = await sentinel.investigate(config.sentinelUrl, payload);
      setProgress(`Investigation ${accepted.investigation_id} accepted — awaiting model output…`);
      const result = await pollInvestigation(config.sentinelUrl, accepted.investigation_id, (n) =>
        setProgress(`Polling for RCA… attempt ${n}`),
      );
      const finished: HistoryRecord = {
        ...record,
        rca: result.rca,
        rawOutput: result.raw_output ?? "",
        savedAt: new Date().toISOString(),
      };
      saveHistoryRecord(finished);
      refreshHistory();
      toast.success("Investigation complete and archived");
      void navigate({ to: "/incidents", search: { id: finished.id } });
    } catch (e) {
      saveHistoryRecord({ ...record, resolutionStatus: "open" });
      refreshHistory();
      toast.error("Sentinel unavailable — payload archived locally", {
        description: e instanceof Error ? e.message : config.sentinelUrl,
      });
    } finally {
      setRunning(false);
      setProgress(null);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Incident & log injection lab</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Craft any custom error payload, dispatch it to Sentinel, and generate structured AI RCA.
          </p>
        </div>
        <Select onValueChange={applyCase}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Load a template or scenario…" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="custom_blank">➕ Blank Custom Form</SelectItem>
            {customTemplates.length > 0 && (
              <>
                <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Your Custom Templates
                </div>
                {customTemplates.map((t) => (
                  <SelectItem key={t.id} value={t.id}>
                    ⭐ {t.label}
                  </SelectItem>
                ))}
              </>
            )}
            <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Predefined Scenarios
            </div>
            {INCIDENT_CASES.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </header>

      <section className="animate-fade-up grid gap-4 rounded-lg border bg-card p-5 md:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="service">Service name</Label>
          <Input
            id="service"
            value={service}
            onChange={(e) => setService(e.target.value)}
            placeholder="orders-api"
          />
        </div>
        <div className="space-y-1.5">
          <Label>Environment</Label>
          <Select value={environment} onValueChange={(v) => setEnvironment(v as Environment)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="production">production</SelectItem>
              <SelectItem value="staging">staging</SelectItem>
              <SelectItem value="dev">dev</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="errorType">Error type</Label>
          <Input
            id="errorType"
            value={errorType}
            onChange={(e) => setErrorType(e.target.value)}
            placeholder="FORM_NOT_FOUND"
            className="font-mono text-xs"
          />
        </div>
        <div className="space-y-1.5">
          <Label>Severity</Label>
          <Select value={severity} onValueChange={(v) => setSeverity(v as Severity)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="critical">critical</SelectItem>
              <SelectItem value="high">high</SelectItem>
              <SelectItem value="medium">medium</SelectItem>
              <SelectItem value="low">low</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5 md:col-span-2">
          <Label htmlFor="errorMessage">Error message</Label>
          <Input
            id="errorMessage"
            value={errorMessage}
            onChange={(e) => setErrorMessage(e.target.value)}
            placeholder="Connection is not available, request timed out after 30000ms"
            className="font-mono text-xs"
          />
        </div>
        <div className="space-y-1.5 md:col-span-2">
          <Label htmlFor="logs">Raw logs</Label>
          <Textarea
            id="logs"
            value={logs}
            onChange={(e) => setLogs(e.target.value)}
            placeholder="One log line per row…"
            className="min-h-40 font-mono text-xs"
          />
        </div>
      </section>

      <section className="animate-fade-up space-y-3 rounded-lg border bg-card p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-tight">Timeline</h2>
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={() => setTimeline([...timeline, { time: "", event: "" }])}
          >
            <Plus className="size-3.5" /> Add item
          </Button>
        </div>
        {timeline.map((t, i) => (
          <div key={i} className="flex gap-2">
            <Input
              value={t.time}
              onChange={(e) =>
                setTimeline(timeline.map((x, xi) => (xi === i ? { ...x, time: e.target.value } : x)))
              }
              placeholder="10:14:02"
              className="w-32 font-mono text-xs"
            />
            <Input
              value={t.event}
              onChange={(e) =>
                setTimeline(
                  timeline.map((x, xi) => (xi === i ? { ...x, event: e.target.value } : x)),
                )
              }
              placeholder="First user task failed to render form"
            />
            <Button
              size="icon"
              variant="ghost"
              onClick={() => setTimeline(timeline.filter((_, xi) => xi !== i))}
            >
              <Trash2 className="size-4" />
            </Button>
          </div>
        ))}
      </section>

      <section
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) void handleFile(file);
        }}
        className={cn(
          "animate-fade-up flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed px-6 py-10 text-center transition-colors",
          dragging ? "border-primary bg-accent" : "bg-card/50 hover:bg-accent/40",
        )}
        onClick={() => fileRef.current?.click()}
      >
        <Upload className="mb-2 size-5 text-muted-foreground" />
        <p className="text-sm font-medium">Drop a .json incident alert file</p>
        <p className="text-xs text-muted-foreground">or click to browse</p>
        <input
          ref={fileRef}
          type="file"
          accept="application/json,.json"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
          }}
        />
      </section>

      {running ? (
        <div className="animate-fade-up rounded-lg border bg-surface px-4 py-3">
          <p className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="size-3.5 animate-spin" /> {progress}
          </p>
          <div className="mt-2 h-0.5 w-full overflow-hidden rounded bg-border">
            <div className="animate-sweep h-full w-1/3 bg-primary" />
          </div>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button className="gap-1.5" disabled={running} onClick={() => void trigger()}>
          {running ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <BrainCircuit className="size-4" />
          )}
          Trigger AI Investigation
        </Button>
        <Button
          variant="outline"
          className="gap-1.5"
          onClick={() => {
            if (!service || !errorType) {
              toast.error("Add a service and error type first");
              return;
            }
            const updated = saveTemplate({
              id: newId("tpl"),
              label: `${errorType} — ${service}`,
              category: "Custom",
              service,
              environment,
              severity,
              errorType,
              errorMessage,
              elementId: "",
              processDefinitionId: "",
              logs: logs.split("\n").filter(Boolean),
              timeline: timeline.filter((t) => t.event).map((t) => `${t.time} — ${t.event}`),
              variables: {},
            });
            setCustomTemplates(updated);
            toast.success("Saved as custom template");
          }}
        >
          <Save className="size-4" /> Save as template
        </Button>
        <Button
          variant="ghost"
          className="gap-1.5"
          onClick={() => {
            setService("");
            setErrorType("");
            setErrorMessage("");
            setLogs("");
            setTimeline([{ time: "", event: "" }]);
          }}
        >
          <FlaskConical className="size-4" /> Clear form
        </Button>
      </div>
    </div>
  );
}
