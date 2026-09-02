# OpenSRE Dashboard — AI SRE & Workflow Incident Management

A 6-page, browser-only frontend that talks directly to your local services (Sentinel :5000, Camunda 8.9 :8080, DGX vLLM :8000) and persists everything else in `localStorage`. No cloud backend, no database — the app runs fully in the browser so it can reach `localhost` on your machine.

## Design direction

Neutral, natural, engineering-grade: warm off-white / graphite palette with a single restrained accent, subtle severity tints (amber / clay / sage) instead of loud reds and greens. JetBrains Mono for keys, IDs and logs; a clean grotesk for UI text. Soft elevation, thin borders, custom slim scrollbars, and quiet motion — fade/slide page transitions, staggered table row entrance, animated status pulses, skeleton loaders, and count-up metric cards. All colors as semantic tokens in `src/styles.css`, dark mode included.

## Pages

**1. Dashboard `/`**
Metric cards (Total Process Instances, Active Incidents, Resolved, History Records Saved, AI Engine Health). Live incidents table (Incident Key, Process, Element ID, Error Type, Created, Actions dropdown). Quick Incident Case dropdown to one-click load a predefined scenario (Missing Form Definition, DMN Evaluation Failure, FEEL Condition Error, DB Pool Exhaustion, Kafka Producer Timeout, HTTP 500 Service Down). System Status widget with live connectivity dots for :8080, :5000, :8000.

**2. Incidents `/incidents`**
Dual pane. Left: case-category selector, filters by Process ID, Error Type (FORM_NOT_FOUND, CONDITION_ERROR, FEELExpressionEvaluationError…), and State (ACTIVE / RESOLVED / SAVED_HISTORY), plus search. Right: full RCA detail — actions dropdown (Resolve in Camunda, Re-run AI Analysis, Save to Local History, Export JSON, Copy Markdown, Delete from History), incident metadata, process-variable inspector (table + JSON tree), WHAT / WHY / Observed Facts / Cited Evidence / HOW to fix (numbered), and an auto-saving Notes + tags area.

**3. History `/history`**
Everything from `localStorage`, browsable offline. Filters by date range, severity, error type, resolution status; search across root causes, error messages and variables; multi-select with batch actions (Export Selected as JSON, Delete Selected, Clear All).

**4. Processes `/processes`**
Deployed BPMN/DMN definitions with Definition Key, Process ID, Version, Active Instances, Incident Count. Detail modal listing running instances and linked incidents.

**5. Ingest Lab `/ingest`**
Predefined case dropdown auto-filling realistic test data; fields for service, environment, error type, error message, raw multi-line logs, and a timeline builder (timestamp + event). `.json` drag-and-drop upload. "Trigger AI Investigation" posts to Sentinel, shows live polling progress, then auto-saves the RCA to history.

**6. Settings `/settings`**
Editable Sentinel / Camunda / DGX URLs, polling interval (5s / 10s / 30s / manual), storage usage meter in KB, Export All Data and Reset Storage.

## Behavior

- Polling every 10s (configurable) of `/v2/incidents/search`, with pause toggle and manual refresh.
- Any successful RCA is written to `localStorage` key `opensre_incident_history` with timestamp and status; notes, tags, custom templates and config live under their own keys.
- Offline resilience: unreachable services show a non-blocking warning badge with retry; the app falls back to saved history so nothing crashes or blanks out.
- Global search across incident messages, element IDs, process names and saved history.

## Technical notes

- TanStack Start routes under `src/routes` (`index`, `incidents`, `history`, `processes`, `ingest`, `settings`) with a shared shell layout (sidebar nav + top status bar) in `__root.tsx`; every route gets its own SEO head().
- All service calls are client-side only (`useEffect` / TanStack Query with `ssr: false` semantics) so `localhost` resolves on the user's machine, never on the server.
- `src/lib/api/{sentinel,camunda,dgx}.ts` typed clients matching the given contracts; `src/lib/storage.ts` typed localStorage layer with versioned keys and safe JSON parsing; `src/lib/incident-cases.ts` for the predefined scenario fixtures.
- Config (URLs, polling, filters) held in a React context hydrated from localStorage after mount to avoid hydration mismatch.
- shadcn/ui components (table, dropdown-menu, dialog, tabs, slider, badge, sonner toasts) with tokens only — no hardcoded color utilities.

Note: the Lovable preview runs in your browser, so it can reach your local services only when they are running on the same machine; when they are not, the app stays usable in history-only mode.
