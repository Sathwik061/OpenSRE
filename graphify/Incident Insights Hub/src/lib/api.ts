import type {
  CamundaIncident,
  CamundaProcessDefinition,
  CamundaProcessInstance,
  CamundaVariable,
  InvestigatePayload,
  InvestigationResult,
} from "./types";

const TIMEOUT_MS = 8000;

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      ...init,
      signal: controller.signal,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const text = await res.text();
    return (text ? JSON.parse(text) : {}) as T;
  } finally {
    clearTimeout(timer);
  }
}

const post = <T,>(url: string, body: unknown) =>
  request<T>(url, { method: "POST", body: JSON.stringify(body) });

/* ------------- Sentinel ------------- */

export const sentinel = {
  health: (base: string) =>
    request<{ status: string; service: string; version: string; active_investigations: number }>(
      `${base}/health`,
    ),
  investigate: (base: string, payload: InvestigatePayload) =>
    post<{ status: string; investigation_id: string; poll_url: string }>(
      `${base}/investigate`,
      payload,
    ),
  investigateFromError: (
    base: string,
    payload: {
      service: string;
      error_type: string;
      error_message: string;
      environment: string;
      logs: string[];
    },
  ) =>
    post<{ status: string; investigation_id: string; poll_url: string }>(
      `${base}/investigate/from-error`,
      payload,
    ),
  getInvestigation: (base: string, id: string) =>
    request<InvestigationResult>(`${base}/investigations/${id}`),
};

/* ------------- Camunda ------------- */

interface SearchResponse<T> {
  items?: T[];
  page?: { totalItems?: number };
}

function resolveCamundaUrl(base: string, path: string): string[] {
  // If base points to 8080 directly, browser will hit CORS, so prioritize proxy endpoints
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const candidates = [
    // 1. Sentinel Gateway Proxy (works from any origin, guaranteed CORS)
    `http://localhost:5000/api/camunda${cleanPath}`,
    // 2. Vite Dev Server Proxy (relative URL)
    `/api/camunda${cleanPath}`,
    // 3. Direct URL (works in SSR or if CORS is enabled)
    `${base}${cleanPath}`,
  ];
  return candidates;
}

async function tryPostEndpoints<T>(urls: string[], body: unknown): Promise<T> {
  let lastErr: unknown = null;
  for (const url of urls) {
    try {
      return await post<T>(url, body);
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr;
}

export const camunda = {
  searchIncidents: async (base: string, state?: string, limit = 50) => {
    const body: Record<string, unknown> = { page: { limit } };
    if (state && state !== "ALL") body["filter"] = { state };
    const urls = resolveCamundaUrl(base, "/v2/incidents/search");
    try {
      const res = await tryPostEndpoints<SearchResponse<CamundaIncident>>(urls, body);
      const items = res.items ?? [];

      // Auto-attach any Sentinel cached RCA in parallel
      const enriched = await Promise.all(
        items.map(async (item) => {
          let rca = item.rca;
          let rawOutput = item.rawOutput;
          try {
            // Try lookup by processInstanceKey or incidentKey
            const lookupKey = item.processInstanceKey || item.incidentKey;
            const inv = await sentinel.getInvestigation("http://localhost:5000", lookupKey);
            if (inv && inv.rca) {
              rca = inv.rca;
              rawOutput = inv.raw_output;
            }
          } catch {
            /* ignore individual rca fetch error */
          }
          return {
            ...item,
            incidentKey: item.incidentKey,
            processInstanceKey: item.processInstanceKey,
            rca,
            rawOutput,
          };
        }),
      );
      return enriched;
    } catch (e) {
      console.warn("Failed to fetch Camunda incidents:", e);
      return [];
    }
  },
  searchProcessInstances: async (base: string, limit = 50) => {
    const body = { page: { limit } };
    const urls = resolveCamundaUrl(base, "/v2/process-instances/search");
    try {
      const res = await tryPostEndpoints<SearchResponse<CamundaProcessInstance>>(urls, body);
      return res.items ?? [];
    } catch (e) {
      console.warn("Failed to fetch Camunda process instances:", e);
      return [];
    }
  },
  searchProcessDefinitions: async (base: string, limit = 50) => {
    const body = { page: { limit } };
    const urls = resolveCamundaUrl(base, "/v2/process-definitions/search");
    try {
      const res = await tryPostEndpoints<SearchResponse<CamundaProcessDefinition>>(urls, body);
      return res.items ?? [];
    } catch (e) {
      console.warn("Failed to fetch Camunda process definitions:", e);
      return [];
    }
  },
  searchVariables: async (base: string, processInstanceKey: string, limit = 100) => {
    const body = {
      filter: { processInstanceKey },
      page: { limit },
    };
    const urls = resolveCamundaUrl(base, "/v2/variables/search");
    try {
      const res = await tryPostEndpoints<SearchResponse<CamundaVariable>>(urls, body);
      return res.items ?? [];
    } catch (e) {
      console.warn("Failed to fetch Camunda variables:", e);
      return [];
    }
  },
  resolveIncident: async (base: string, incidentKey: string) => {
    const urls = resolveCamundaUrl(base, `/v2/incidents/${incidentKey}/resolution`);
    return tryPostEndpoints<unknown>(urls, {});
  },
  getProcessDefinitionXml: async (base: string, processDefinitionKey: string): Promise<string> => {
    const urls = [
      `http://localhost:5000/api/camunda/v2/process-definitions/${processDefinitionKey}/xml`,
      `http://localhost:5000/api/camunda/process-definitions/${processDefinitionKey}/xml`,
      `${base.replace(/\/+$/, "")}/v2/process-definitions/${processDefinitionKey}/xml`,
    ];
    for (const url of urls) {
      try {
        const res = await fetch(url);
        if (res.ok) {
          const contentType = res.headers.get("content-type") || "";
          if (contentType.includes("json")) {
            const data = await res.json();
            return data.xml || "";
          }
          return await res.text();
        }
      } catch {
        /* try next */
      }
    }
    return "";
  },
};

/* ------------- DGX / vLLM ------------- */

export const dgx = {
  models: async (base: string) => {
    const urls = [
      `http://localhost:5000/api/dgx/models`,
      `/api/dgx/models`,
      `${base}/models`,
    ];
    for (const url of urls) {
      try {
        return await request<{ data?: Array<{ id: string }> }>(url, { method: "GET" });
      } catch {
        // try next candidate
      }
    }
    return { data: [] };
  },

  listRunbooks: async (base: string) => {
    const res = await fetch(`${base.replace(/\/+$/, "")}/api/runbooks`);
    if (!res.ok) throw new Error(`Runbooks API ${res.status}`);
    return res.json() as Promise<{ count: number; runbooks: any[] }>;
  },

  saveRunbook: async (base: string, payload: any) => {
    const res = await fetch(`${base.replace(/\/+$/, "")}/api/runbooks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Failed to save runbook (${res.status})`);
    return res.json();
  },
};

/** Poll a Sentinel investigation until it completes or times out. */
export async function pollInvestigation(
  base: string,
  id: string,
  onTick?: (attempt: number) => void,
  maxAttempts = 30,
  intervalMs = 1200,
): Promise<InvestigationResult> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    onTick?.(attempt);
    try {
      const res = await sentinel.getInvestigation(base, id);
      if (res) {
        if (res.status === "running" || res.status === "pending") {
          // Still in progress
        } else if (res.rca) {
          return res;
        } else if (res.status === "error") {
          if (res.rca) return res;
          throw new Error(res.error || "Investigation failed on backend");
        } else if (res.status === "done" || res.status === "success") {
          return res;
        }
      }
    } catch (err: any) {
      if (err?.message && !err.message.includes("404") && !err.message.includes("running") && !err.message.includes("progress")) {
        throw err;
      }
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error("Investigation timed out waiting for backend response");
}
