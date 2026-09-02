import type { AppConfig, HistoryRecord, IncidentCase } from "./types";

export const STORAGE_KEYS = {
  history: "opensre_incident_history",
  notes: "opensre_incident_notes",
  templates: "opensre_custom_templates",
  config: "opensre_app_config",
} as const;

export const DEFAULT_CONFIG: AppConfig = {
  sentinelUrl: "http://localhost:5000",
  camundaUrl: "http://localhost:8080",
  dgxUrl: "http://localhost:8000/v1",
  pollingIntervalMs: 10000,
  pollingEnabled: true,
  defaultStateFilter: "ALL",
};

const hasWindow = () => typeof window !== "undefined";

function read<T>(key: string, fallback: T): T {
  if (!hasWindow()) return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function write(key: string, value: unknown) {
  if (!hasWindow()) return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    window.dispatchEvent(new CustomEvent("opensre:storage", { detail: { key } }));
  } catch (err) {
    console.error("localStorage write failed", err);
  }
}

/* ---------------- history ---------------- */

export function getHistory(): HistoryRecord[] {
  return read<HistoryRecord[]>(STORAGE_KEYS.history, []);
}

export function saveHistoryRecord(record: HistoryRecord): HistoryRecord[] {
  const all = getHistory();
  const idx = all.findIndex((r) => r.id === record.id);
  if (idx >= 0) all[idx] = { ...all[idx], ...record };
  else all.unshift(record);
  write(STORAGE_KEYS.history, all);
  return all;
}

export function updateHistoryRecord(id: string, patch: Partial<HistoryRecord>): HistoryRecord[] {
  const all = getHistory().map((r) => (r.id === id ? { ...r, ...patch } : r));
  write(STORAGE_KEYS.history, all);
  return all;
}

export function deleteHistoryRecords(ids: string[]): HistoryRecord[] {
  const set = new Set(ids);
  const all = getHistory().filter((r) => !set.has(r.id));
  write(STORAGE_KEYS.history, all);
  return all;
}

export function clearHistory(): HistoryRecord[] {
  write(STORAGE_KEYS.history, []);
  return [];
}

/* ---------------- notes ---------------- */

export function getNotes(): Record<string, string> {
  return read<Record<string, string>>(STORAGE_KEYS.notes, {});
}

export function setNote(key: string, note: string) {
  write(STORAGE_KEYS.notes, { ...getNotes(), [key]: note });
}

/* ---------------- custom templates ---------------- */

export function getTemplates(): IncidentCase[] {
  return read<IncidentCase[]>(STORAGE_KEYS.templates, []);
}

export function saveTemplate(tpl: IncidentCase): IncidentCase[] {
  const all = getTemplates().filter((t) => t.id !== tpl.id);
  all.unshift(tpl);
  write(STORAGE_KEYS.templates, all);
  return all;
}

export function deleteTemplate(id: string): IncidentCase[] {
  const all = getTemplates().filter((t) => t.id !== id);
  write(STORAGE_KEYS.templates, all);
  return all;
}

/* ---------------- config ---------------- */

export function getConfig(): AppConfig {
  return { ...DEFAULT_CONFIG, ...read<Partial<AppConfig>>(STORAGE_KEYS.config, {}) };
}

export function setConfig(cfg: AppConfig) {
  write(STORAGE_KEYS.config, cfg);
}

/* ---------------- utilities ---------------- */

export function storageUsageBytes(): number {
  if (!hasWindow()) return 0;
  return Object.values(STORAGE_KEYS).reduce((total, key) => {
    const raw = window.localStorage.getItem(key);
    return total + (raw ? new Blob([raw]).size : 0);
  }, 0);
}

export function exportAllData() {
  return {
    exportedAt: new Date().toISOString(),
    history: getHistory(),
    notes: getNotes(),
    templates: getTemplates(),
    config: getConfig(),
  };
}

export function resetAllStorage() {
  if (!hasWindow()) return;
  Object.values(STORAGE_KEYS).forEach((k) => window.localStorage.removeItem(k));
  window.dispatchEvent(new CustomEvent("opensre:storage", { detail: { key: "*" } }));
}

export function downloadJson(filename: string, data: unknown) {
  if (!hasWindow()) return;
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
