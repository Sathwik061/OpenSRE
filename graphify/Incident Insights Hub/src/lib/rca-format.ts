import type { HistoryRecord } from "./types";

export function recordToMarkdown(r: HistoryRecord): string {
  const lines: string[] = [];
  lines.push(`# RCA — ${r.title}`);
  lines.push("");
  lines.push(`- **Service:** ${r.service}`);
  lines.push(`- **Environment:** ${r.environment}`);
  lines.push(`- **Severity:** ${r.severity}`);
  lines.push(`- **Error type:** ${r.errorType}`);
  if (r.processDefinitionId) lines.push(`- **Process definition:** ${r.processDefinitionId}`);
  if (r.processInstanceKey) lines.push(`- **Instance key:** ${r.processInstanceKey}`);
  if (r.elementId) lines.push(`- **Element:** ${r.elementId}`);
  lines.push(`- **Saved at:** ${r.savedAt}`);
  lines.push("");
  lines.push(`## WHAT is the error?`);
  lines.push(r.rca?.summary ?? r.errorMessage);
  lines.push("");
  if (r.rca) {
    lines.push(`## WHY did it occur?`);
    lines.push(r.rca.root_cause);
    lines.push("");
    lines.push(`## Observed facts`);
    r.rca.observed_facts?.forEach((f) => lines.push(`- ${f}`));
    lines.push("");
    lines.push(`## Cited evidence`);
    r.rca.evidence?.forEach((e) => lines.push(`- \`${e}\``));
    lines.push("");
    lines.push(`## HOW to fix it`);
    r.rca.recommended_actions?.forEach((a, i) => lines.push(`${i + 1}. ${a}`));
    lines.push("");
    if (r.rca.documentation_references && r.rca.documentation_references.length > 0) {
      const ver = r.rca.camunda_version || r.camunda_version || r.payload?.camunda_version || "8.9";
      lines.push(`## Camunda ${ver} Documentation References`);
      r.rca.documentation_references.forEach((doc) => {
        lines.push(`- **${doc.section || doc.title || "Camunda Doc"}:** ${doc.url ?? ""} — ${doc.relevance ?? ""}`);
      });
      lines.push("");
    }
    lines.push(`_Confidence: ${r.rca.confidence}_`);
  }
  if (r.notes) {
    lines.push("");
    lines.push(`## Notes`);
    lines.push(r.notes);
  }
  return lines.join("\n");
}

export function formatTime(value?: string) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function relativeTime(value?: string) {
  if (!value) return "—";
  const d = new Date(value).getTime();
  if (Number.isNaN(d)) return value;
  const diff = Date.now() - d;
  const mins = Math.round(diff / 60000);
  if (Math.abs(mins) < 1) return "just now";
  if (Math.abs(mins) < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (Math.abs(hours) < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}
