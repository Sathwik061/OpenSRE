import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Archive, ChevronDown, Download, Search, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState } from "@/components/EmptyState";
import { SeverityBadge, TypeChip } from "@/components/SeverityBadge";
import { useApp } from "@/lib/app-context";
import { formatTime } from "@/lib/rca-format";
import { clearHistory, deleteHistoryRecords, downloadJson } from "@/lib/storage";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "Investigation History & Archive — OpenSRE" },
      {
        name: "description",
        content:
          "Search, filter and export every archived RCA investigation stored locally in your browser, even while backend services are offline.",
      },
      { property: "og:title", content: "Investigation History & Archive — OpenSRE" },
      {
        property: "og:description",
        content: "Offline archive of every AI root cause investigation you have run.",
      },
    ],
  }),
  component: HistoryPage,
});

function HistoryPage() {
  const navigate = useNavigate();
  const { history, refreshHistory } = useApp();
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("ALL");
  const [errorType, setErrorType] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const errorTypes = useMemo(
    () => Array.from(new Set(history.map((h) => h.errorType).filter(Boolean))),
    [history],
  );

  const filtered = history.filter((h) => {
    if (severity !== "ALL" && h.severity !== severity) return false;
    if (errorType !== "ALL" && h.errorType !== errorType) return false;
    if (status !== "ALL" && h.resolutionStatus !== status) return false;
    const ts = new Date(h.savedAt).getTime();
    if (from && ts < new Date(from).getTime()) return false;
    if (to && ts > new Date(to).getTime() + 86400000) return false;
    if (query) {
      const hay = [
        h.title,
        h.errorMessage,
        h.rca?.root_cause,
        h.rca?.summary,
        h.notes,
        JSON.stringify(h.variables ?? {}),
      ]
        .join(" ")
        .toLowerCase();
      if (!hay.includes(query.toLowerCase())) return false;
    }
    return true;
  });

  const allChecked = filtered.length > 0 && filtered.every((f) => selected.includes(f.id));

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Investigation history</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {history.length} records archived in local storage · fully searchable offline.
          </p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-1.5">
              Batch actions <ChevronDown className="size-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>{selected.length} selected</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              disabled={selected.length === 0}
              onSelect={() =>
                downloadJson(
                  `opensre-history-${Date.now()}.json`,
                  history.filter((h) => selected.includes(h.id)),
                )
              }
            >
              <Download className="size-4" /> Export Selected as JSON
            </DropdownMenuItem>
            <DropdownMenuItem
              disabled={selected.length === 0}
              onSelect={() => {
                deleteHistoryRecords(selected);
                setSelected([]);
                refreshHistory();
                toast.success("Selected records deleted");
              }}
            >
              <Trash2 className="size-4" /> Delete Selected
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onSelect={() => {
                clearHistory();
                setSelected([]);
                refreshHistory();
                toast.success("All history cleared");
              }}
            >
              <Trash2 className="size-4" /> Clear All History
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      <div className="animate-fade-up grid gap-2 rounded-lg border bg-card p-3 md:grid-cols-6">
        <div className="relative md:col-span-2">
          <Search className="absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search root causes, errors, variables…"
            className="pl-8"
          />
        </div>
        <Select value={severity} onValueChange={setSeverity}>
          <SelectTrigger>
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All severities</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
        <Select value={errorType} onValueChange={setErrorType}>
          <SelectTrigger>
            <SelectValue placeholder="Error type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All error types</SelectItem>
            {errorTypes.map((t) => (
              <SelectItem key={t} value={t}>
                {t}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger>
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Any status</SelectItem>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="investigating">Investigating</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
          </SelectContent>
        </Select>
        <div className="flex gap-2">
          <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className="text-xs" />
          <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} className="text-xs" />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={Archive}
          title="No archived investigations"
          description="Run an investigation from the Ingest Lab or open an incident RCA to start building your offline archive."
        />
      ) : (
        <div className="animate-fade-up overflow-hidden rounded-lg border bg-card">
          <table className="w-full text-sm">
            <thead className="bg-surface/95">
              <tr className="text-left text-[10px] uppercase tracking-wider text-muted-foreground">
                <th className="w-10 px-3 py-2">
                  <Checkbox
                    checked={allChecked}
                    onCheckedChange={(v) =>
                      setSelected(v ? filtered.map((f) => f.id) : [])
                    }
                  />
                </th>
                <th className="px-3 py-2 font-medium">Incident</th>
                <th className="px-3 py-2 font-medium">Error type</th>
                <th className="px-3 py-2 font-medium">Severity</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">Saved</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((h, i) => (
                <tr
                  key={h.id}
                  className="animate-fade-up border-t transition-colors hover:bg-accent/40"
                  style={{ animationDelay: `${Math.min(i * 25, 250)}ms` }}
                >
                  <td className="px-3 py-2">
                    <Checkbox
                      checked={selected.includes(h.id)}
                      onCheckedChange={(v) =>
                        setSelected((s) => (v ? [...s, h.id] : s.filter((x) => x !== h.id)))
                      }
                    />
                  </td>
                  <td className="max-w-72 px-3 py-2">
                    <p className="truncate text-sm font-medium">{h.title}</p>
                    <p className="truncate font-mono text-[11px] text-muted-foreground">
                      {h.errorMessage}
                    </p>
                  </td>
                  <td className="px-3 py-2">
                    <TypeChip value={h.errorType} />
                  </td>
                  <td className="px-3 py-2">
                    <SeverityBadge severity={h.severity} />
                  </td>
                  <td className="px-3 py-2 font-mono text-[11px] text-muted-foreground">
                    {h.resolutionStatus}
                  </td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">
                    {formatTime(h.savedAt)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => void navigate({ to: "/incidents", search: { id: h.id } })}
                    >
                      Open
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
