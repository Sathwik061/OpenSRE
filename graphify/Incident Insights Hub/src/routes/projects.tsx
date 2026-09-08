import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Briefcase,
  Plus,
  Search,
  Server,
  FileText,
  Trash2,
  ExternalLink,
  ShieldCheck,
  Cpu,
  Layers,
  CheckCircle2,
  AlertCircle,
  FileCode,
  UploadCloud,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useApp } from "@/lib/app-context";

export const Route = createFileRoute("/projects")({
  head: () => ({
    meta: [
      { title: "Project Passports — OpenSRE" },
      {
        name: "description",
        content:
          "Project Intake & Context Profiling Framework: capture business intent, architecture dependencies, and multi-format runbooks.",
      },
    ],
  }),
  component: ProjectsPage,
});

interface Dependency {
  name: string;
  dep_type: string;
  description?: string;
  endpoint?: string;
  critical: boolean;
}

interface AttachedRunbook {
  id: string;
  filename: string;
  title: string;
  format: string;
  uploaded_at: string;
  size_bytes?: number;
}

interface ProjectProfile {
  id: string;
  name: string;
  slug: string;
  business_purpose: string;
  platform: string;
  platform_version?: string;
  environment: string;
  owner_team?: string;
  notification_channels?: string[];
  dependencies?: Dependency[];
  attached_runbooks?: AttachedRunbook[];
  active_integrations?: string[];
  created_at?: string;
}

function ProjectsPage() {
  const { config } = useApp();
  const sentinelBase = config.sentinelUrl || "http://localhost:5000";

  const [projects, setProjects] = useState<ProjectProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("all");

  // Modal State
  const [createOpen, setCreateOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [formName, setFormName] = useState("");
  const [formPurpose, setFormPurpose] = useState("");
  const [formPlatform, setFormPlatform] = useState("camunda-8");
  const [formVersion, setFormVersion] = useState("8.9");
  const [formEnvironment, setFormEnvironment] = useState("production");
  const [formOwnerTeam, setFormOwnerTeam] = useState("SRE Core Team");
  const [formChannels, setFormChannels] = useState("#sre-critical, #eng-alerts");
  const [formDeps, setFormDeps] = useState<Dependency[]>([
    { name: "PostgreSQL Database", dep_type: "database", critical: true },
    { name: "Redis Cache Cluster", dep_type: "cache", critical: false },
  ]);

  // Runbook Upload in modal
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${sentinelBase}/api/projects`);
      if (res.ok) {
        const data = await res.json();
        setProjects(data.projects || []);
      } else {
        toast.error("Could not fetch project registry from Sentinel.");
      }
    } catch (e) {
      toast.error("Failed to connect to Sentinel project API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [sentinelBase]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim() || !formPurpose.trim()) {
      toast.error("Project name and business purpose are required.");
      return;
    }

    try {
      setSubmitting(true);
      const channels = formChannels.split(",").map((c) => c.trim()).filter(Boolean);
      const payload = {
        name: formName.trim(),
        business_purpose: formPurpose.trim(),
        platform: formPlatform,
        platform_version: formVersion.trim() || "1.0",
        environment: formEnvironment,
        owner_team: formOwnerTeam.trim() || "SRE Team",
        notification_channels: channels,
        dependencies: formDeps,
      };

      const res = await fetch(`${sentinelBase}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create project");
      }

      const created = await res.json();

      // If a runbook document was attached during creation, upload it
      if (uploadFile && created.id) {
        const formData = new FormData();
        formData.append("file", uploadFile);
        formData.append("project_id", created.id);
        formData.append("title", `${formName} SOP Document`);
        await fetch(`${sentinelBase}/api/runbooks/upload`, {
          method: "POST",
          body: formData,
        });
      }

      toast.success(`Project Passport '${formName}' registered successfully!`);
      setCreateOpen(false);
      resetForm();
      fetchProjects();
    } catch (e: any) {
      toast.error(e.message || "Failed to save project.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteProject = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete Project Passport '${name}'?`)) return;
    try {
      const res = await fetch(`${sentinelBase}/api/projects/${id}`, { method: "DELETE" });
      if (res.ok) {
        toast.success(`Project '${name}' deleted.`);
        fetchProjects();
      } else {
        toast.error("Failed to delete project.");
      }
    } catch (e) {
      toast.error("Error deleting project.");
    }
  };

  const resetForm = () => {
    setFormName("");
    setFormPurpose("");
    setFormPlatform("camunda-8");
    setFormVersion("8.9");
    setFormEnvironment("production");
    setFormOwnerTeam("SRE Core Team");
    setFormChannels("#sre-critical, #eng-alerts");
    setUploadFile(null);
  };

  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.business_purpose.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.platform.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPlatform =
      selectedPlatform === "all" || p.platform.toLowerCase().includes(selectedPlatform.toLowerCase());
    return matchesSearch && matchesPlatform;
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex size-7 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Briefcase className="size-4" />
            </span>
            <h1 className="text-2xl font-semibold tracking-tight">Project Passports</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Project Intake & Context Profiling Framework. Captures business purpose ("motto"), technology stack,
            architecture dependencies, and links to attached multi-format runbooks (PDF / Word).
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="gap-2">
          <Plus className="size-4" /> Register Project Passport
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Registered Passports</span>
            <Layers className="size-4 text-primary" />
          </div>
          <p className="mt-2 text-2xl font-semibold tracking-tight">{projects.length}</p>
          <p className="text-xs text-muted-foreground">Universal profiling catalog</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Production Tier-1</span>
            <ShieldCheck className="size-4 text-emerald-500" />
          </div>
          <p className="mt-2 text-2xl font-semibold tracking-tight">
            {projects.filter((p) => p.environment === "production").length}
          </p>
          <p className="text-xs text-muted-foreground">Mission-critical services</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Attached Runbooks</span>
            <FileText className="size-4 text-blue-500" />
          </div>
          <p className="mt-2 text-2xl font-semibold tracking-tight">
            {projects.reduce((acc, p) => acc + (p.attached_runbooks?.length || 0), 0)}
          </p>
          <p className="text-xs text-muted-foreground">PDF & Word .docx SOPs</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Target Platforms</span>
            <Cpu className="size-4 text-violet-500" />
          </div>
          <p className="mt-2 text-2xl font-semibold tracking-tight">
            {new Set(projects.map((p) => p.platform)).size}
          </p>
          <p className="text-xs text-muted-foreground">Camunda, Pega, K8s, Custom</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search projects by name, intent, or platform..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">Platform:</span>
          <Select value={selectedPlatform} onValueChange={setSelectedPlatform}>
            <SelectTrigger className="w-[170px]">
              <SelectValue placeholder="All Platforms" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Platforms</SelectItem>
              <SelectItem value="camunda">Camunda (8 & 7)</SelectItem>
              <SelectItem value="pega">Pega Platform</SelectItem>
              <SelectItem value="kubernetes">Kubernetes</SelectItem>
              <SelectItem value="temporal">Temporal</SelectItem>
              <SelectItem value="custom">Custom Engine</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="py-16 text-center text-muted-foreground">Loading Project Passports...</div>
      ) : filteredProjects.length === 0 ? (
        <div className="rounded-xl border border-dashed py-16 text-center">
          <Server className="mx-auto size-10 text-muted-foreground" />
          <h3 className="mt-3 text-base font-medium">No Project Passports found</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Register your first service to attach business purpose and runbooks for AI investigation.
          </p>
          <Button onClick={() => setCreateOpen(true)} variant="outline" className="mt-4 gap-2">
            <Plus className="size-4" /> Register New Project
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {filteredProjects.map((proj) => (
            <div
              key={proj.id}
              className="flex flex-col justify-between rounded-lg border bg-card p-5 transition-shadow hover:shadow-md"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold tracking-tight text-foreground">{proj.name}</h3>
                    <p className="font-mono text-xs text-muted-foreground">ID: {proj.id}</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Badge variant="outline" className="capitalize">
                      {proj.platform} {proj.platform_version ? `v${proj.platform_version}` : ""}
                    </Badge>
                    <Badge
                      className={
                        proj.environment === "production"
                          ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                          : "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20"
                      }
                      variant="outline"
                    >
                      {proj.environment}
                    </Badge>
                  </div>
                </div>

                {/* Business Purpose ("Why it was built") */}
                <div className="mt-3 rounded-md bg-muted/40 p-3 text-xs leading-relaxed text-foreground/90">
                  <span className="font-semibold text-primary">Operational Intent: </span>
                  {proj.business_purpose || "No business purpose documented."}
                </div>

                {/* Dependencies */}
                {proj.dependencies && proj.dependencies.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-muted-foreground">Architecture Dependencies:</p>
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {proj.dependencies.map((dep, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 rounded bg-secondary px-2 py-0.5 text-[11px] font-medium"
                        >
                          <span
                            className={`size-1.5 rounded-full ${
                              dep.critical ? "bg-amber-500" : "bg-muted-foreground"
                            }`}
                          />
                          {dep.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Attached Runbooks */}
                <div className="mt-3">
                  <p className="text-xs font-medium text-muted-foreground">Attached Runbooks:</p>
                  {proj.attached_runbooks && proj.attached_runbooks.length > 0 ? (
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {proj.attached_runbooks.map((rb) => (
                        <span
                          key={rb.id}
                          className="inline-flex items-center gap-1 rounded-md border bg-background px-2 py-1 text-xs text-foreground"
                        >
                          <FileCode className="size-3 text-primary" />
                          <span className="max-w-[180px] truncate">{rb.title || rb.filename}</span>
                          <span className="font-mono text-[10px] text-muted-foreground uppercase">
                            ({rb.format})
                          </span>
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-1 text-xs italic text-muted-foreground">
                      No document runbooks attached yet.
                    </p>
                  )}
                </div>
              </div>

              {/* Bottom footer */}
              <div className="mt-5 flex items-center justify-between border-t pt-3">
                <span className="text-xs text-muted-foreground">
                  Owner: <span className="font-medium text-foreground">{proj.owner_team || "SRE Team"}</span>
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteProject(proj.id, proj.name)}
                    className="size-8 p-0 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Register New Project Passport</DialogTitle>
            <DialogDescription>
              Define your service's business purpose, architectural dependencies, and attach SOPs to empower
              the OpenSRE root cause analysis engine.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCreateProject} className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="proj-name">Service / Process Name *</Label>
              <Input
                id="proj-name"
                placeholder="e.g. orderFulfillmentProcess or Global Payment API"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="proj-purpose">
                Business Purpose / Moto ("Why it was built") *
              </Label>
              <Textarea
                id="proj-purpose"
                placeholder="Describe what this workflow or service does in real business terms. For example: Orchestrates high-volume credit card checkouts, reserving warehouse stock and dispatching real-time notifications."
                rows={3}
                value={formPurpose}
                onChange={(e) => setFormPurpose(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="proj-platform">Target Platform</Label>
                <Select value={formPlatform} onValueChange={setFormPlatform}>
                  <SelectTrigger id="proj-platform">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="camunda-8">Camunda 8 (Zeebe)</SelectItem>
                    <SelectItem value="camunda-7">Camunda 7 (Classic)</SelectItem>
                    <SelectItem value="pega">Pega Platform</SelectItem>
                    <SelectItem value="kubernetes">Kubernetes</SelectItem>
                    <SelectItem value="temporal">Temporal.io</SelectItem>
                    <SelectItem value="custom">Custom Framework</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="proj-env">Environment</Label>
                <Select value={formEnvironment} onValueChange={setFormEnvironment}>
                  <SelectTrigger id="proj-env">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="production">Production</SelectItem>
                    <SelectItem value="staging">Staging</SelectItem>
                    <SelectItem value="development">Development</SelectItem>
                    <SelectItem value="dr">Disaster Recovery (DR)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="proj-owner">Owner Team</Label>
                <Input
                  id="proj-owner"
                  value={formOwnerTeam}
                  onChange={(e) => setFormOwnerTeam(e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="proj-channels">Alert Channels</Label>
                <Input
                  id="proj-channels"
                  value={formChannels}
                  onChange={(e) => setFormChannels(e.target.value)}
                  placeholder="#sre-critical, #ops"
                />
              </div>
            </div>

            {/* Runbook Upload Dropzone */}
            <div className="space-y-1.5">
              <Label>Attach Enterprise Runbook (PDF / Word .docx)</Label>
              <div className="flex items-center gap-3 rounded-md border border-dashed p-3">
                <UploadCloud className="size-6 text-muted-foreground" />
                <div className="flex-1">
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc,.txt,.md"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="text-xs file:mr-2 file:rounded-md file:border-0 file:bg-primary/10 file:px-2 file:py-1 file:text-xs file:font-medium file:text-primary hover:file:bg-primary/20"
                  />
                  {uploadFile && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Selected: <span className="font-semibold text-foreground">{uploadFile.name}</span> ({(uploadFile.size / 1024).toFixed(1)} KB)
                    </p>
                  )}
                </div>
              </div>
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Registering..." : "Save Project Passport"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
