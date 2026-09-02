import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { camunda, dgx, sentinel } from "./api";
import {
  DEFAULT_CONFIG,
  getConfig,
  getHistory,
  setConfig as persistConfig,
} from "./storage";
import type { AppConfig, HistoryRecord, ServiceStatus } from "./types";

interface AppContextValue {
  config: AppConfig;
  updateConfig: (patch: Partial<AppConfig>) => void;
  hydrated: boolean;
  history: HistoryRecord[];
  refreshHistory: () => void;
  statuses: { camunda: ServiceStatus; sentinel: ServiceStatus; dgx: ServiceStatus };
  aiModel: string | null;
  checkStatuses: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [config, setConfigState] = useState<AppConfig>(DEFAULT_CONFIG);
  const [hydrated, setHydrated] = useState(false);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [aiModel, setAiModel] = useState<string | null>(null);
  const [statuses, setStatuses] = useState<AppContextValue["statuses"]>({
    camunda: "checking",
    sentinel: "checking",
    dgx: "checking",
  });

  const refreshHistory = useCallback(() => setHistory(getHistory()), []);

  useEffect(() => {
    setConfigState(getConfig());
    setHistory(getHistory());
    setHydrated(true);
    const onStorage = () => setHistory(getHistory());
    window.addEventListener("opensre:storage", onStorage);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("opensre:storage", onStorage);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const updateConfig = useCallback((patch: Partial<AppConfig>) => {
    setConfigState((prev) => {
      const next = { ...prev, ...patch };
      persistConfig(next);
      return next;
    });
  }, []);

  const checkStatuses = useCallback(() => {
    if (typeof window === "undefined") return;
    const probe = async (
      key: keyof AppContextValue["statuses"],
      fn: () => Promise<unknown>,
      after?: (v: unknown) => void,
    ) => {
      try {
        const v = await fn();
        after?.(v);
        setStatuses((s) => ({ ...s, [key]: "online" }));
      } catch {
        setStatuses((s) => ({ ...s, [key]: "offline" }));
        if (key === "dgx") setAiModel(null);
      }
    };
    void probe("camunda", () => camunda.searchProcessDefinitions(config.camundaUrl, 1));
    void probe("sentinel", () => sentinel.health(config.sentinelUrl));
    void probe("dgx", () => dgx.models(config.dgxUrl), (v) => {
      const data = (v as { data?: Array<{ id: string }> })?.data;
      setAiModel(data?.[0]?.id ?? "model");
    });
  }, [config.camundaUrl, config.sentinelUrl, config.dgxUrl]);

  useEffect(() => {
    if (!hydrated) return;
    checkStatuses();
    const interval = window.setInterval(checkStatuses, 30000);
    return () => window.clearInterval(interval);
  }, [hydrated, checkStatuses]);

  const value = useMemo(
    () => ({ config, updateConfig, hydrated, history, refreshHistory, statuses, aiModel, checkStatuses }),
    [config, updateConfig, hydrated, history, refreshHistory, statuses, aiModel, checkStatuses],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}
