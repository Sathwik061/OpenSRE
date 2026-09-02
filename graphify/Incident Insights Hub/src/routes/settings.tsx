import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Database, Download, RefreshCw, RotateCcw, Save } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { StatusPill } from "@/components/StatusDot";
import { useApp } from "@/lib/app-context";
import {
  DEFAULT_CONFIG,
  downloadJson,
  exportAllData,
  resetAllStorage,
  storageUsageBytes,
} from "@/lib/storage";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings & Diagnostics — OpenSRE" },
      {
        name: "description",
        content:
          "Configure Sentinel, Camunda and DGX endpoints, polling frequency and manage local storage for the OpenSRE console.",
      },
      { property: "og:title", content: "Settings & Diagnostics — OpenSRE" },
      {
        property: "og:description",
        content: "Backend endpoints, polling controls and local storage management.",
      },
    ],
  }),
  component: SettingsPage,
});

const INTERVALS = [5000, 10000, 30000, 60000];

function SettingsPage() {
  const { config, updateConfig, statuses, checkStatuses, refreshHistory, history } = useApp();
  const [draft, setDraft] = useState(config);
  const [usage, setUsage] = useState(0);

  useEffect(() => setDraft(config), [config]);
  useEffect(() => setUsage(storageUsageBytes()), [history]);

  const intervalIndex = Math.max(0, INTERVALS.indexOf(draft.pollingIntervalMs));

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Settings & diagnostics</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Point the console at your local services and manage the offline archive.
        </p>
      </header>

      <section className="animate-fade-up space-y-4 rounded-lg border bg-card p-5">
        <h2 className="text-sm font-semibold tracking-tight">Backend endpoints</h2>
        {(
          [
            ["sentinelUrl", "Sentinel RCA URL", "http://localhost:5000"],
            ["camundaUrl", "Camunda REST URL", "http://localhost:8080"],
            ["dgxUrl", "DGX vLLM URL", "http://localhost:8000/v1"],
          ] as const
        ).map(([key, label, placeholder]) => (
          <div key={key} className="space-y-1.5">
            <Label htmlFor={key} className="text-xs uppercase tracking-wider text-muted-foreground">
              {label}
            </Label>
            <Input
              id={key}
              value={draft[key]}
              placeholder={placeholder}
              onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
              className="font-mono text-xs"
            />
          </div>
        ))}
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            className="gap-1.5"
            onClick={() => {
              updateConfig(draft);
              toast.success("Configuration saved");
              window.setTimeout(checkStatuses, 200);
            }}
          >
            <Save className="size-3.5" /> Save configuration
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={checkStatuses}>
            <RefreshCw className="size-3.5" /> Test connections
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="gap-1.5"
            onClick={() => setDraft({ ...draft, ...DEFAULT_CONFIG })}
          >
            <RotateCcw className="size-3.5" /> Restore defaults
          </Button>
        </div>
        <div className="grid gap-2 pt-1 sm:grid-cols-3">
          <StatusPill label="Camunda" status={statuses.camunda} detail=":8080" />
          <StatusPill label="Sentinel" status={statuses.sentinel} detail=":5000" />
          <StatusPill label="DGX AI" status={statuses.dgx} detail=":8000" />
        </div>
      </section>

      <section className="animate-fade-up space-y-4 rounded-lg border bg-card p-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold tracking-tight">Polling</h2>
            <p className="text-xs text-muted-foreground">
              Auto-refresh of incidents, instances and definitions.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Auto</span>
            <Switch
              checked={draft.pollingEnabled}
              onCheckedChange={(v) => {
                setDraft({ ...draft, pollingEnabled: v });
                updateConfig({ pollingEnabled: v });
              }}
            />
          </div>
        </div>
        <div className="space-y-3">
          <Slider
            value={[intervalIndex]}
            min={0}
            max={INTERVALS.length - 1}
            step={1}
            onValueChange={([v]) => {
              const ms = INTERVALS[v ?? 1] ?? 10000;
              setDraft({ ...draft, pollingIntervalMs: ms });
              updateConfig({ pollingIntervalMs: ms });
            }}
          />
          <div className="flex justify-between font-mono text-[11px] text-muted-foreground">
            {INTERVALS.map((ms) => (
              <span key={ms} className={ms === draft.pollingIntervalMs ? "text-primary" : ""}>
                {ms / 1000}s
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="animate-fade-up space-y-4 rounded-lg border bg-card p-5">
        <div className="flex items-center gap-2">
          <Database className="size-4 text-primary" />
          <h2 className="text-sm font-semibold tracking-tight">Local storage</h2>
        </div>
        <div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{(usage / 1024).toFixed(1)} KB used</span>
            <span>{history.length} records · soft limit 5000 KB</span>
          </div>
          <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${Math.min(100, (usage / 1024 / 5000) * 100)}%` }}
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={() => downloadJson(`opensre-export-${Date.now()}.json`, exportAllData())}
          >
            <Download className="size-3.5" /> Export all data
          </Button>
          <Button
            size="sm"
            variant="destructive"
            className="gap-1.5"
            onClick={() => {
              resetAllStorage();
              refreshHistory();
              setUsage(0);
              toast.success("Local storage reset");
            }}
          >
            <RotateCcw className="size-3.5" /> Reset storage
          </Button>
        </div>
      </section>
    </div>
  );
}
