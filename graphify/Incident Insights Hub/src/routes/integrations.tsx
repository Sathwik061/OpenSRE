import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Blocks,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  KeyRound,
  Trash2,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Zap,
  Activity,
  Server,
  Database,
  MessageSquare,
  FileText,
  GitCommit,
  Lock,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useApp } from "@/lib/app-context";

export const Route = createFileRoute("/integrations")({
  head: () => ({
    meta: [
      { title: "Enterprise Integrations Hub — OpenSRE" },
      {
        name: "description",
        content:
          "Connect 60+ enterprise integrations across Observability, Workflows, Cloud, Databases, ITSM, and ChatOps with 3-tier secrets encryption.",
      },
    ],
  }),
  component: IntegrationsPage,
});

interface IntegrationField {
  key: string;
  label: string;
  type: string;
  required: boolean;
  placeholder?: string;
  description?: string;
}

interface IntegrationItem {
  id: string;
  name: string;
  category: string;
  tier: number;
  description: string;
  icon: string;
  capabilities: string[];
  required_fields: IntegrationField[];
  doc_url?: string;
  website?: string;
  is_configured: boolean;
  configured_credentials?: Record<string, string>;
}

const CATEGORIES = [
  "All",
  "Observability",
  "Workflow",
  "Collaboration",
  "Cloud & Infra",
  "Incident & ITSM",
  "Databases & Queues",
  "CI/CD & Code",
  "Security & Secrets",
];

function IntegrationsPage() {
  const { config } = useApp();
  const sentinelBase = config.sentinelUrl || "http://localhost:5000";

  const [integrations, setIntegrations] = useState<IntegrationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  // Config modal
  const [activeItem, setActiveItem] = useState<IntegrationItem | null>(null);
  const [formCreds, setFormCreds] = useState<Record<string, string>>({});
  const [pinging, setPinging] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pingResult, setPingResult] = useState<{
    success: boolean;
    latency_ms: number;
    message: string;
  } | null>(null);

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${sentinelBase}/api/integrations`);
      if (res.ok) {
        const data = await res.json();
        setIntegrations(data.integrations || []);
      } else {
        toast.error("Could not fetch integrations catalog from Sentinel.");
      }
    } catch (e) {
      toast.error("Failed to connect to Sentinel Integrations API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, [sentinelBase]);

  const handleOpenConfig = (item: IntegrationItem) => {
    setActiveItem(item);
    setPingResult(null);
    const initial: Record<string, string> = {};
    item.required_fields.forEach((f) => {
      initial[f.key] = item.configured_credentials?.[f.key] || "";
    });
    setFormCreds(initial);
  };

  const handleTestPing = async () => {
    if (!activeItem) return;
    try {
      setPinging(true);
      setPingResult(null);
      const res = await fetch(`${sentinelBase}/api/integrations/${activeItem.id}/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credentials: formCreds }),
      });
      const data = await res.json();
      setPingResult({
        success: data.success,
        latency_ms: data.latency_ms || 0,
        message: data.message || (data.success ? "Connection successful" : "Failed"),
      });
      if (data.success) {
        toast.success(`Ping test passed (${data.latency_ms}ms)`);
      } else {
        toast.error(data.message || "Connectivity test failed.");
      }
    } catch (e: any) {
      toast.error(e.message || "Failed to execute ping test.");
    } finally {
      setPinging(false);
    }
  };

  const handleSaveConfig = async () => {
    if (!activeItem) return;
    try {
      setSaving(true);
      const res = await fetch(`${sentinelBase}/api/integrations/${activeItem.id}/configure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credentials: formCreds }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to configure integration.");
      }
      toast.success(`${activeItem.name} configured and encrypted in 3-tier vault!`);
      setActiveItem(null);
      fetchIntegrations();
    } catch (e: any) {
      toast.error(e.message || "Failed to save configuration.");
    } finally {
      setSaving(false);
    }
  };

  const handleDisconnect = async (id: string, name: string) => {
    if (!confirm(`Revoke and purge credentials for ${name}?`)) return;
    try {
      const res = await fetch(`${sentinelBase}/api/integrations/${id}`, { method: "DELETE" });
      if (res.ok) {
        toast.success(`${name} credentials purged from vault.`);
        if (activeItem?.id === id) setActiveItem(null);
        fetchIntegrations();
      } else {
        toast.error("Failed to disconnect integration.");
      }
    } catch (e) {
      toast.error("Error purging credentials.");
    }
  };

  const filteredItems = integrations.filter((item) => {
    const matchesCategory =
      selectedCategory === "All" || item.category.toLowerCase() === selectedCategory.toLowerCase();
    const matchesSearch =
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const configuredCount = integrations.filter((i) => i.is_configured).length;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex size-7 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Blocks className="size-4" />
            </span>
            <h1 className="text-2xl font-semibold tracking-tight">Enterprise Integrations Hub</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Connect OpenSRE to 60+ platforms across Observability, Workflows, Cloud, Databases, and ChatOps.
            Protected by a 3-tier AES-GCM encrypted vault with clean asterisk credential masking.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-primary/20 bg-primary/5 px-3 py-1 font-mono text-xs text-primary">
            {configuredCount} / {integrations.length} Active
          </Badge>
          <Button variant="outline" size="sm" onClick={fetchIntegrations} className="gap-1.5">
            <RefreshCw className="size-3.5" /> Refresh
          </Button>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-col gap-3">
        <div className="overflow-x-auto pb-1">
          <div className="flex gap-1.5">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors ${
                  selectedCategory === cat
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Search Filter */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search 60+ integrations (e.g. Datadog, Slack, Camunda, K8s)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Grid of Integration Cards */}
      {loading ? (
        <div className="py-16 text-center text-muted-foreground">Loading integrations catalog...</div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-xl border border-dashed py-16 text-center">
          <Blocks className="mx-auto size-10 text-muted-foreground" />
          <h3 className="mt-3 text-base font-medium">No integrations found</h3>
          <p className="mt-1 text-sm text-muted-foreground">Try adjusting your search query or category filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="flex flex-col justify-between rounded-lg border bg-card p-5 transition-shadow hover:shadow-md"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className="flex size-9 items-center justify-center rounded-lg bg-secondary text-foreground">
                      <Zap className="size-4 text-primary" />
                    </span>
                    <div>
                      <h3 className="text-base font-semibold tracking-tight text-foreground">{item.name}</h3>
                      <span className="text-[11px] text-muted-foreground">{item.category}</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    {item.is_configured ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                        <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        Connected
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                        Ready
                      </span>
                    )}
                    <span className="text-[10px] font-mono text-muted-foreground uppercase">
                      Tier {item.tier}
                    </span>
                  </div>
                </div>

                <p className="mt-3 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                  {item.description}
                </p>

                {/* Capabilities */}
                <div className="mt-3 flex flex-wrap gap-1">
                  {item.capabilities.slice(0, 3).map((cap) => (
                    <span
                      key={cap}
                      className="rounded bg-secondary/80 px-1.5 py-0.5 font-mono text-[10px] text-secondary-foreground"
                    >
                      {cap.replace(/_/g, " ")}
                    </span>
                  ))}
                  {item.capabilities.length > 3 && (
                    <span className="rounded bg-secondary/80 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                      +{item.capabilities.length - 3}
                    </span>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <div className="mt-5 flex items-center justify-between border-t pt-3">
                {item.doc_url ? (
                  <a
                    href={item.doc_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                  >
                    API Docs <ExternalLink className="size-3" />
                  </a>
                ) : (
                  <span />
                )}
                <div className="flex items-center gap-1.5">
                  <Button
                    variant={item.is_configured ? "outline" : "default"}
                    size="sm"
                    onClick={() => handleOpenConfig(item)}
                    className="text-xs"
                  >
                    {item.is_configured ? "Manage & Test" : "Connect"}
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Configuration & Test Ping Modal */}
      {activeItem && (
        <Dialog open={!!activeItem} onOpenChange={(open) => !open && setActiveItem(null)}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <div className="flex items-center gap-2">
                <span className="flex size-7 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Zap className="size-4" />
                </span>
                <DialogTitle>Configure {activeItem.name}</DialogTitle>
              </div>
              <DialogDescription>
                Credentials are AES-256 encrypted in the 3-tier secrets vault. Plaintext tokens are cleanly
                masked as asterisks.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-2">
              {activeItem.required_fields.map((field) => (
                <div key={field.key} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor={field.key} className="text-xs font-medium">
                      {field.label} {field.required && <span className="text-destructive">*</span>}
                    </Label>
                    {field.type === "password" && (
                      <span className="flex items-center gap-1 font-mono text-[10px] text-muted-foreground">
                        <Lock className="size-2.5" /> 3-Tier Encrypted
                      </span>
                    )}
                  </div>
                  <Input
                    id={field.key}
                    type={field.type === "password" ? "password" : "text"}
                    placeholder={field.placeholder || ""}
                    value={formCreds[field.key] || ""}
                    onChange={(e) => setFormCreds({ ...formCreds, [field.key]: e.target.value })}
                  />
                  {field.description && (
                    <p className="text-[11px] text-muted-foreground">{field.description}</p>
                  )}
                </div>
              ))}

              {/* Ping Result Banner */}
              {pingResult && (
                <div
                  className={`flex items-start gap-2.5 rounded-lg border p-3 text-xs ${
                    pingResult.success
                      ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                      : "border-destructive/20 bg-destructive/10 text-destructive"
                  }`}
                >
                  {pingResult.success ? (
                    <CheckCircle2 className="size-4 shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5" />
                  ) : (
                    <AlertCircle className="size-4 shrink-0 text-destructive mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className="font-semibold">
                      {pingResult.success ? "Connectivity Verified" : "Verification Failed"}
                      {pingResult.latency_ms > 0 && ` (${pingResult.latency_ms}ms)`}
                    </p>
                    <p className="mt-0.5 text-[11px] opacity-90">{pingResult.message}</p>
                  </div>
                </div>
              )}
            </div>

            <DialogFooter className="flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-between">
              {activeItem.is_configured ? (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => handleDisconnect(activeItem.id, activeItem.name)}
                  className="text-destructive hover:bg-destructive/10 text-xs"
                >
                  <Trash2 className="mr-1.5 size-3.5" /> Revoke & Disconnect
                </Button>
              ) : (
                <span />
              )}
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleTestPing}
                  disabled={pinging}
                  className="gap-1.5 text-xs"
                >
                  <Activity className="size-3.5" />
                  {pinging ? "Pinging..." : "Test Connectivity"}
                </Button>
                <Button
                  type="button"
                  onClick={handleSaveConfig}
                  disabled={saving}
                  className="gap-1.5 text-xs"
                >
                  <ShieldCheck className="size-3.5" />
                  {saving ? "Encrypting..." : "Save to Vault"}
                </Button>
              </div>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
