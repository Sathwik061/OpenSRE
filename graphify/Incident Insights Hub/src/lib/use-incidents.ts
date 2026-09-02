import { useCallback, useEffect, useRef, useState } from "react";
import { camunda } from "./api";
import { useApp } from "./app-context";
import type { CamundaIncident, CamundaProcessDefinition, CamundaProcessInstance } from "./types";

export function useCamundaData() {
  const { config, hydrated } = useApp();
  const [incidents, setIncidents] = useState<CamundaIncident[]>([]);
  const [instances, setInstances] = useState<CamundaProcessInstance[]>([]);
  const [definitions, setDefinitions] = useState<CamundaProcessDefinition[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const refresh = useCallback(async () => {
    if (typeof window === "undefined") return;
    setLoading(true);
    try {
      const [inc, inst, defs] = await Promise.all([
        camunda.searchIncidents(config.camundaUrl),
        camunda.searchProcessInstances(config.camundaUrl),
        camunda.searchProcessDefinitions(config.camundaUrl),
      ]);
      if (!mounted.current) return;
      setIncidents(inc);
      setInstances(inst);
      setDefinitions(defs);
      setError(null);
      setLastUpdated(new Date().toISOString());
    } catch (e) {
      if (!mounted.current) return;
      setError(e instanceof Error ? e.message : "Camunda unreachable");
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, [config.camundaUrl]);

  useEffect(() => {
    if (!hydrated) return;
    void refresh();
  }, [hydrated, refresh]);

  useEffect(() => {
    if (!hydrated || paused || !config.pollingEnabled) return;
    const id = window.setInterval(() => void refresh(), config.pollingIntervalMs);
    return () => window.clearInterval(id);
  }, [hydrated, paused, config.pollingEnabled, config.pollingIntervalMs, refresh]);

  return {
    incidents,
    instances,
    definitions,
    error,
    loading,
    lastUpdated,
    paused,
    setPaused,
    refresh,
  };
}
