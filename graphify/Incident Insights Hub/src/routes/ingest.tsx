import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import {
  BrainCircuit,
  FlaskConical,
  Loader2,
  Plus,
  Save,
  Trash2,
  Upload,
  Briefcase,
  FileText,
  FileCode,
  UploadCloud,
  CheckCircle2,
  Globe,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
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
import { maskStringValue, maskVariables } from "@/lib/masking";
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

  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("none");
  const [activeProject, setActiveProject] = useState<any>(null);
  const [uploadedRunbooks, setUploadedRunbooks] = useState<string[]>([]);

  const [service, setService] = useState("");
  const [environment, setEnvironment] = useState<Environment>("production");
  const [severity, setSeverity] = useState<Severity>("high");
  const [camundaVersion, setCamundaVersion] = useState("8.9");
  const [errorType, setErrorType] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [logs, setLogs] = useState("");
  const [timeline, setTimeline] = useState<TimelineItem[]>([{ time: "", event: "" }]);
  const [variables, setVariables] = useState<Record<string, any>>({});
  const [elementId, setElementId] = useState("");
  const [instanceKey, setInstanceKey] = useState("");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [customTemplates, setCustomTemplates] = useState<IncidentCase[]>(() => getTemplates());

  useEffect(() => {
    fetch(`${config.sentinelUrl || "http://localhost:5000"}/api/projects`)
      .then((r) => r.json())
      .then((data) => {
        if (data.projects) setProjects(data.projects);
      })
      .catch(() => {});
  }, [config.sentinelUrl]);

  function handleSelectProject(projId: string) {
    setSelectedProjectId(projId);
    if (projId === "none") {
      setActiveProject(null);
      return;
    }
    const found = projects.find((p) => p.id === projId);
    if (found) {
      setActiveProject(found);
      setService(found.name);
      setEnvironment(found.environment as Environment);
      if (found.platform_version) setCamundaVersion(found.platform_version);
      toast.success(`Context loaded from Project Passport: ${found.name}`);
    }
  }

  function applyCase(id: string) {
    if (id === "custom_blank") {
      setService("");
      setErrorType("");
      setErrorMessage("");
      setLogs("");
      setVariables({});
      setElementId("");
      setInstanceKey("");
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
    setVariables(c.variables || {});
    setElementId(c.elementId || "");
    setInstanceKey(c.processInstanceKey || "");
    setTimeline(
      c.timeline.map((t) => {
        const [time, ...rest] = t.split(" — ");
        return { time: time ?? "", event: rest.join(" — ") };
      }),
    );
    toast.success("Case loaded", { description: c.label });
  }

  async function handleFile(file: File) {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext === "pdf" || ext === "docx" || ext === "doc") {
      try {
        const formData = new FormData();
        formData.append("file", file);
        if (selectedProjectId && selectedProjectId !== "none") {
          formData.append("project_id", selectedProjectId);
        }
        formData.append("title", file.name);
        const res = await fetch(`${config.sentinelUrl || "http://localhost:5000"}/api/runbooks/upload`, {
          method: "POST",
          body: formData,
        });
        if (res.ok) {
          const up = await res.json();
          setUploadedRunbooks((prev) => [...prev, file.name]);
          toast.success(`Runbook uploaded & indexed (${up.chunks_indexed || 1} chunks)`, {
            description: `${file.name} is now active for local AI RAG`,
          });
          return;
        } else {
          toast.error("Failed to parse runbook document.");
        }
      } catch (err: any) {
        toast.error("Error uploading document: " + err.message);
      }
      return;
    }

    try {
      const rawText = await file.text();
      // 1. Try parsing as JSON first
      try {
        const parsed = JSON.parse(rawText) as Record<string, unknown>;
        if (typeof parsed === "object" && parsed !== null) {
          if (parsed["service"] || parsed["alert_name"]) {
            setService(String(parsed["service"] ?? parsed["alert_name"] ?? ""));
          }
          if (parsed["error"] || parsed["error_type"]) {
            setErrorType(String(parsed["error"] ?? parsed["error_type"] ?? ""));
          }
          if (parsed["error_message"] || parsed["message"]) {
            setErrorMessage(String(parsed["error_message"] ?? parsed["message"] ?? ""));
          }
          if (parsed["camunda_version"] || parsed["version"]) {
            setCamundaVersion(String(parsed["camunda_version"] ?? parsed["version"]));
          }
          if (parsed["element_id"]) {
            setElementId(String(parsed["element_id"]));
          }
          if (parsed["instance_key"]) {
            setInstanceKey(String(parsed["instance_key"]));
          }
          if (parsed["variables"] && typeof parsed["variables"] === "object") {
            setVariables(parsed["variables"] as Record<string, any>);
          }
          if (Array.isArray(parsed["logs"])) {
            setLogs((parsed["logs"] as string[]).join("\n"));
          } else if (typeof parsed["logs"] === "string") {
            setLogs(parsed["logs"]);
          }
          if (Array.isArray(parsed["timeline"])) {
            setTimeline(
              (parsed["timeline"] as string[]).map((t) => {
                const [time, ...rest] = String(t).split(" — ");
                return { time: time ?? "", event: rest.join(" — ") };
              }),
            );
          }
          toast.success("Incident alert file loaded", { description: file.name });
          return;
        }
      } catch {
        // Not JSON, treat as raw log file (.log / .txt)
      }

      // 2. Parse as Plain Text Log file (.log)
      setLogs(rawText);
      const lines = rawText.split("\n").map((l) => l.trim()).filter(Boolean);

      // Extract filename base as fallback service
      const cleanFileName = file.name.replace(/\.(log|txt|json)$/i, "").replace(/[-_]/g, " ");

      // Detect version in logs or filename (e.g. Camunda 8.6, 8.9)
      const verMatch = rawText.match(/Camunda\s*([89]\.[0-9]+)/i) || file.name.match(/8[._-]([0-9]+)/);
      if (verMatch) {
        if (verMatch[1].includes(".")) {
          setCamundaVersion(verMatch[1]);
        } else {
          setCamundaVersion(`8.${verMatch[1]}`);
        }
      }

      // Regex patterns to detect service name
      let detectedService = "";
      const serviceMatch =
        rawText.match(/\[([a-zA-Z0-9_\-]+(?:-service|-worker|-process|Process|Service))\]/i) ||
        rawText.match(/service[=:]\s*["']?([a-zA-Z0-9_\-]+)["']?/i) ||
        rawText.match(/processDefinition[=:]\s*["']?([a-zA-Z0-9_\-]+)["']?/i);
      if (serviceMatch && serviceMatch[1]) {
        detectedService = serviceMatch[1];
      } else {
        detectedService = cleanFileName || "orderProcess";
      }
      setService(detectedService);

      // Regex patterns to detect error type
      let detectedErrorType = "";
      const knownErrors = [
        "UNHANDLED_ERROR_EVENT",
        "DECISION_EVALUATION_ERROR",
        "CONDITION_ERROR",
        "JOB_NO_RETRIES",
        "FORM_NOT_FOUND",
        "CALLED_ELEMENT_ERROR",
        "MESSAGE_CORRELATION_ERROR",
        "PaymentGatewayTimeout",
        "DatabaseConnectionPoolExhausted",
        "ConnectionTimeoutException",
        "NullPointerException",
        "DeadlockException",
        "FEEL_EVALUATION_ERROR",
      ];
      for (const err of knownErrors) {
        if (rawText.includes(err)) {
          detectedErrorType = err;
          break;
        }
      }
      if (!detectedErrorType) {
        const errMatch = rawText.match(/([A-Z][a-zA-Z0-9]*(?:Exception|Error|Timeout|Exhausted|Failure))/);
        if (errMatch && errMatch[1]) {
          detectedErrorType = errMatch[1];
        } else {
          detectedErrorType = "APPLICATION_ERROR";
        }
      }
      setErrorType(detectedErrorType);

      // Extract primary error message (prioritizing FATAL/incident description over WARN lines)
      let detectedMessage = "";
      const fatalOrIncidentLine = lines.find((l) => /FATAL|CRITICAL/i.test(l) || l.includes(detectedErrorType) || /Expected to throw/i.test(l));
      const explicitErrorLine = lines.find((l) => /\[ERROR\]/i.test(l) && !/\[WARN\]/i.test(l));
      const genericErrorLine = lines.find((l) => /ERROR|Exception|Timeout|Failed|failed/i.test(l) && !/\[WARN\]/i.test(l));

      const chosenLine = fatalOrIncidentLine || explicitErrorLine || genericErrorLine || lines.find((l) => /ERROR|FATAL|Exception|Timeout/i.test(l));
      if (chosenLine) {
        const chosenIndex = lines.indexOf(chosenLine);
        // Check if the next line provides the detailed incident reason (e.g. 'Expected to throw an error event...')
        const nextLine = chosenIndex >= 0 && chosenIndex + 1 < lines.length ? lines[chosenIndex + 1] : "";
        if (nextLine && (/Expected to throw/i.test(nextLine) || /No error boundary/i.test(nextLine) || /caused by/i.test(nextLine))) {
          detectedMessage = nextLine.trim();
        } else {
          detectedMessage = chosenLine
            .replace(/^\[?[0-9T:.\-Z ]+\]?\s*(?:\[[A-Z]+\]\s*)?(?:\[[a-zA-Z0-9_\-]+\]\s*)?/i, "")
            .trim();
        }
      } else if (lines.length > 0) {
        detectedMessage = lines[0] ?? "";
      }
      setErrorMessage(detectedMessage || `Incident detected in ${detectedService}`);

      // Extract elementId if present in logs
      const elementMatch =
        rawText.match(/elementId[:=\s'"]+([a-zA-Z0-9_\-]+)/i) ||
        rawText.match(/scope of element ['"]([a-zA-Z0-9_\-]+)['"]/i) ||
        rawText.match(/flowNodeId[:=\s'"]+([a-zA-Z0-9_\-]+)/i);
      if (elementMatch && elementMatch[1]) {
        setElementId(elementMatch[1]);
      }

      // Extract instanceKey if present in logs
      const instanceMatch =
        rawText.match(/instance(?:Key|_key)?[:=\s'"]+(\d{10,25})/i) ||
        rawText.match(/processInstanceKey[:=\s'"]+(\d{10,25})/i);
      if (instanceMatch && instanceMatch[1]) {
        setInstanceKey(instanceMatch[1]);
      }

      // Extract timeline events from timestamps
      const timelineEntries: TimelineItem[] = [];
      const timestampRegex = /(\b\d{2}:\d{2}:\d{2}(?:\.\d{3})?|\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})/;
      for (const line of lines) {
        const match = line.match(timestampRegex);
        if (match && match[1] && timelineEntries.length < 5) {
          const time =
            match[1].includes("T") || match[1].includes("-")
              ? match[1].split(/[T ]/)[1]?.substring(0, 8) ?? match[1]
              : match[1];
          const eventText = line
            .replace(match[0], "")
            .replace(/^\[?[A-Z]+\]?\s*/, "")
            .replace(/^\[?[a-zA-Z0-9_\-]+\]?\s*/, "")
            .trim();
          if (eventText) {
            timelineEntries.push({ time, event: eventText.substring(0, 120) });
          }
        }
      }
      if (timelineEntries.length > 0) {
        setTimeline(timelineEntries);
      }

      toast.success("Log file loaded and parsed", { description: file.name });
    } catch {
      toast.error("Could not process uploaded file");
    }
  }

  async function trigger() {
    if (!service || !errorType) {
      toast.error("Service name and error type are required");
      return;
    }
    const maskedErrorMessage = maskStringValue(errorMessage);
    const maskedLogs = logs.split("\n").filter(Boolean).map((l) => maskStringValue(l));
    const maskedTimeline = timeline.filter((t) => t.event).map((t) => `${t.time} — ${maskStringValue(t.event)}`);
    const maskedVariables = maskVariables(variables);

    const payload = {
      alert_name: `${errorType} in ${service}`,
      service,
      environment,
      error: errorType,
      error_message: maskedErrorMessage,
      logs: maskedLogs,
      timeline: maskedTimeline,
      severity,
      camunda_version: camundaVersion,
      element_id: elementId,
      instance_key: instanceKey,
      variables: maskedVariables,
      project_id: selectedProjectId !== "none" ? selectedProjectId : undefined,
      request: `Investigate ${errorType} in ${service} (${environment}) on Camunda ${camundaVersion}`,
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
      errorMessage: maskedErrorMessage,
      elementId,
      processInstanceKey: instanceKey,
      variables: maskedVariables,
      resolutionStatus: "investigating",
      creationTime: new Date().toISOString(),
      payload,
      camunda_version: camundaVersion,
    };

    setRunning(true);
    setProgress("Dispatching payload to Sentinel…");
    try {
      const accepted = await sentinel.investigate(config.sentinelUrl, payload);
      setProgress(`Investigation ${accepted.investigation_id} accepted — awaiting model output…`);
      const result = await pollInvestigation(config.sentinelUrl, accepted.investigation_id, (n) =>
        setProgress(`Polling for RCA… attempt ${n}`),
      );
      const rcaVersion = result.camunda_version || result.rca?.camunda_version || camundaVersion;
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

      const finished: HistoryRecord = {
        ...record,
        camunda_version: rcaVersion,
        rca: enhancedRca,
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

      {/* Project Passport Context & Multi-Format Runbook Ingestion Banner */}
      <section className="animate-fade-up rounded-lg border border-primary/20 bg-primary/5 p-4 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Briefcase className="size-4" />
            </span>
            <div>
              <h3 className="text-sm font-semibold tracking-tight text-foreground">
                Project Passport Context & Runbook Ingestion
              </h3>
              <p className="text-xs text-muted-foreground">
                Link this incident to a registered service profile or upload PDF / Word runbooks for live RAG.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Select value={selectedProjectId} onValueChange={handleSelectProject}>
              <SelectTrigger className="w-64 bg-background text-xs">
                <SelectValue placeholder="Select Project Passport..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">-- Standalone Service --</SelectItem>
                {projects.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    📁 {p.name} ({p.platform})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {activeProject && (
          <div className="mt-3 rounded-md border border-primary/20 bg-background/80 p-3 text-xs leading-relaxed">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-primary">Operational Intent ("Why it was built"):</span>
              <div className="flex items-center gap-1.5 font-mono text-[10px]">
                <Badge variant="outline">{activeProject.platform}</Badge>
                <Badge variant="outline" className="text-emerald-600">{activeProject.environment}</Badge>
              </div>
            </div>
            <p className="mt-1 text-foreground/90">{activeProject.business_purpose}</p>
            {activeProject.dependencies && activeProject.dependencies.length > 0 && (
              <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                <span className="text-muted-foreground font-medium">Dependencies:</span>
                {activeProject.dependencies.map((d: any, idx: number) => (
                  <span key={idx} className="inline-flex items-center gap-1 rounded bg-secondary px-1.5 py-0.5 text-[10px]">
                    <span className={`size-1.5 rounded-full ${d.critical ? 'bg-amber-500' : 'bg-muted-foreground'}`} />
                    {d.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {uploadedRunbooks.length > 0 && (
          <div className="mt-2 flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
            <CheckCircle2 className="size-3.5" />
            <span>Active Uploaded Runbooks: {uploadedRunbooks.join(", ")}</span>
          </div>
        )}
      </section>

      <section className="animate-fade-up grid gap-4 rounded-lg border bg-card p-5 md:grid-cols-3">
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
          <Label>Camunda version</Label>
          <Select value={camundaVersion} onValueChange={setCamundaVersion}>
            <SelectTrigger>
              <SelectValue placeholder="Camunda 8.9" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="8.9">Camunda 8.9 (Current)</SelectItem>
              <SelectItem value="8.8">Camunda 8.8</SelectItem>
              <SelectItem value="8.7">Camunda 8.7</SelectItem>
              <SelectItem value="8.6">Camunda 8.6</SelectItem>
              <SelectItem value="8.5">Camunda 8.5</SelectItem>
              <SelectItem value="8.4">Camunda 8.4</SelectItem>
              <SelectItem value="8.10">Camunda 8.10 (Upcoming)</SelectItem>
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
        <div className="space-y-1.5 md:col-span-3">
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
        <p className="text-sm font-medium">Drop any incident log (.log, .json) or enterprise runbook (.pdf, .docx, .doc)</p>
        <p className="text-xs text-muted-foreground">or click to browse — automatic multi-format parsing & local RAG indexing</p>
        <input
          ref={fileRef}
          type="file"
          accept=".log,.txt,.json,.pdf,.docx,.doc,text/plain,application/json,application/pdf"
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
