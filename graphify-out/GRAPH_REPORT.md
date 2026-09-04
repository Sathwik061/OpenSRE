# Graph Report - Open SRE  (2026-09-04)

## Corpus Check
- 207 files · ~57,491 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1019 nodes · 1650 edges · 109 communities (60 shown, 49 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dca3699d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- RcaDetail.tsx
- devDependencies
- camunda_bridge.py
- form.tsx
- sidebar.tsx
- routeTree.gen.ts
- incident_registry.py
- compilerOptions
- GraphifyHook
- LogFileTailer
- supabase_runbook.py
- test_sentinel.py
- MetricCard.tsx
- utils.ts
- components.json
- server.ts
- run_investigation
- investigate_from_error
- command.tsx
- menubar.tsx
- _print_rca
- post
- cn
- main.py
- dependencies
- watcher.py
- context-menu.tsx
- alert-dialog.tsx
- table.tsx
- breadcrumb.tsx
- drawer.tsx
- navigation-menu.tsx
- worker.py
- OpenSRE + Camunda 8 + DGX AI Agent — Complete Documentation
- toggle-group.tsx
- alert.tsx
- OpenSRE (Graphify) — Product Presentation & Demo Script
- carousel.tsx
- tabs.tsx
- bpmn-js
- class-variance-authority
- clsx
- cmdk
- embla-carousel-react
- @hookform/resolvers
- lucide-react
- @radix-ui/react-accordion
- @radix-ui/react-alert-dialog
- @radix-ui/react-aspect-ratio
- @radix-ui/react-avatar
- @radix-ui/react-collapsible
- @radix-ui/react-context-menu
- @radix-ui/react-dialog
- @radix-ui/react-dropdown-menu
- @radix-ui/react-hover-card
- @radix-ui/react-label
- @radix-ui/react-menubar
- processes.tsx
- @radix-ui/react-popover
- @radix-ui/react-progress
- @radix-ui/react-scroll-area
- @radix-ui/react-select
- @radix-ui/react-separator
- @radix-ui/react-slider
- @radix-ui/react-slot
- @radix-ui/react-switch
- @radix-ui/react-tabs
- @radix-ui/react-toggle
- @radix-ui/react-toggle-group
- @radix-ui/react-tooltip
- react-day-picker
- react-dom
- react-hook-form
- react-resizable-panels
- sonner
- tailwind-merge
- tailwindcss
- @tailwindcss/vite
- @tanstack/react-query
- @tanstack/react-router
- @tanstack/react-start
- tw-animate-css
- vaul
- vite-tsconfig-paths
- zod
- chart.tsx
- sheet.tsx
- Graphify — Real-Time Camunda 8 SRE Incident Remediation
- react
- OpenSRE Dashboard — AI SRE & Workflow Incident Management
- Welcome to your Lovable project
- input-otp.tsx
- Routes
- date-fns
- tooltip.tsx

## God Nodes (most connected - your core abstractions)
1. `cn()` - 88 edges
2. `compilerOptions` - 22 edges
3. `useApp()` - 19 edges
4. `run_bridge()` - 17 edges
5. `_get()` - 17 edges
6. `Button` - 12 edges
7. `saveHistoryRecord()` - 11 edges
8. `OpenSRE + Camunda 8 + DGX AI Agent — Complete Documentation` - 11 edges
9. `write()` - 10 edges
10. `downloadJson()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `AlertDialogHeader()` --calls--> `cn()`  [EXTRACTED]
  graphify/Incident Insights Hub/src/components/ui/alert-dialog.tsx → graphify/Incident Insights Hub/src/lib/utils.ts
- `AlertDialogFooter()` --calls--> `cn()`  [EXTRACTED]
  graphify/Incident Insights Hub/src/components/ui/alert-dialog.tsx → graphify/Incident Insights Hub/src/lib/utils.ts
- `BreadcrumbSeparator()` --calls--> `cn()`  [EXTRACTED]
  graphify/Incident Insights Hub/src/components/ui/breadcrumb.tsx → graphify/Incident Insights Hub/src/lib/utils.ts
- `BreadcrumbEllipsis()` --calls--> `cn()`  [EXTRACTED]
  graphify/Incident Insights Hub/src/components/ui/breadcrumb.tsx → graphify/Incident Insights Hub/src/lib/utils.ts
- `CommandShortcut()` --calls--> `cn()`  [EXTRACTED]
  graphify/Incident Insights Hub/src/components/ui/command.tsx → graphify/Incident Insights Hub/src/lib/utils.ts

## Import Cycles
- None detected.

## Communities (109 total, 49 thin omitted)

### Community 0 - "RcaDetail.tsx"
Cohesion: 0.05
Nodes (96): AppShell(), NAV, EmptyState(), OperateBpmnViewer(), OperateBpmnViewerProps, RcaDetail(), SeverityBadge(), StateChip() (+88 more)

### Community 1 - "devDependencies"
Cohesion: 0.04
Nodes (48): eslint, eslint-config-prettier, @eslint/js, eslint-plugin-prettier, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals, devDependencies (+40 more)

### Community 2 - "camunda_bridge.py"
Cohesion: 0.07
Nodes (43): build_incident_payload(), check_dgx_alive(), check_operate_alive(), fetch_bpmn_xml(), fetch_flow_node_name(), fetch_instance_variables(), fetch_live_incidents(), fetch_process_instance() (+35 more)

### Community 3 - "form.tsx"
Cohesion: 0.15
Nodes (11): FormControl, FormDescription, FormFieldContext, FormFieldContextValue, FormItem, FormItemContext, FormItemContextValue, FormLabel (+3 more)

### Community 4 - "sidebar.tsx"
Cohesion: 0.07
Nodes (27): Separator, Sidebar, SidebarContent, SidebarContext, SidebarContextProps, SidebarFooter, SidebarGroup, SidebarGroupAction (+19 more)

### Community 5 - "routeTree.gen.ts"
Cohesion: 0.07
Nodes (32): Toaster(), ToasterProps, LovableErrorOptions, LovableEvents, reportLovableError(), Window, getRouter(), Route (+24 more)

### Community 6 - "incident_registry.py"
Cohesion: 0.10
Nodes (36): async_main(), deploy_bpmn(), _now(), camunda/deploy.py — Camunda 8 Zeebe Deploy & Trigger…, Deploy the BPMN definition to Zeebe via gRPC., Create a process instance in Zeebe with dynamic incident variables., trigger_incident(), _api_gateway_500() (+28 more)

### Community 7 - "compilerOptions"
Cohesion: 0.06
Nodes (31): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, jsx, lib, module, moduleResolution, noEmit (+23 more)

### Community 8 - "GraphifyHook"
Cohesion: 0.11
Nodes (17): _build_payload(), GraphifyHook, _now(), error_hook.py — Graphify Auto-Error Interceptor…, Installs a global exception hook that forwards all unhandled exceptions to the…, Install the global exception hook. Args: service: Name of your service/app…, Remove the hook and restore original excepthook., Manually trigger an RCA investigation without raising an exception. Useful for… (+9 more)

### Community 9 - "LogFileTailer"
Cohesion: 0.13
Nodes (15): generate_demo_log(), LogFileTailer, main(), Path, log_watcher.py — Graphify Log File Auto-Watcher…, Tails a log file and triggers RCA when error patterns are detected. Buffers…, Send buffered error lines to Sentinel., Start or reset the batch timer. (+7 more)

### Community 10 - "supabase_runbook.py"
Cohesion: 0.11
Nodes (29): get_investigation(), Retrieve the result or status of a specific investigation. Returns…, seed_predefined_runbooks.py — Seed Predefined Open SRE Runbooks into Supabase…, seed(), _bump_use_count(), delete_runbook(), _get(), _headers() (+21 more)

### Community 11 - "test_sentinel.py"
Cohesion: 0.11
Nodes (18): fixture, auth_error_event(), payment_incident(), tests/test_sentinel.py Smoke tests for the Sentinel FastAPI service. Run:…, Verify the response includes the path to the saved incident file., Verify the /investigate/from-error endpoint builds and investigates., Incomplete payload should return 422 Unprocessable Entity., Return current UTC timestamp in log format. (+10 more)

### Community 13 - "utils.ts"
Cohesion: 0.07
Nodes (16): AccordionContent, AccordionItem, AccordionTrigger, Avatar, AvatarFallback, AvatarImage, Checkbox, HoverCardContent (+8 more)

### Community 14 - "components.json"
Cohesion: 0.11
Nodes (18): aliases, components, hooks, lib, ui, utils, iconLibrary, registries (+10 more)

### Community 15 - "server.ts"
Cohesion: 0.17
Nodes (13): consumeLastCapturedError(), describeError(), describeStatus(), originalConsoleError, safeStringify(), renderErrorPage(), fetch(), getServerEntry() (+5 more)

### Community 16 - "run_investigation"
Cohesion: 0.14
Nodes (17): get_active_model(), investigate_with_dgx(), is_dgx_available(), sentinel/dgx_engine.py ====================== Direct integration with company…, Check if the local SSH tunnel to DGX vLLM is active on port 8000., Detect the active model name from the vLLM /models endpoint., Run Root Cause Analysis using company DGX vLLM endpoint. Returns parsed JSON…, _build_env() (+9 more)

### Community 17 - "investigate_from_error"
Cohesion: 0.16
Nodes (16): BackgroundTasks, BaseModel, build_incident_from_error(), Converts a raw ErrorEvent (from Camunda or a webhook) into a fully-formed…, investigate(), investigate_from_error(), Worker function: runs the investigation and stores the result. Called in a…, Run an RCA investigation on a fully-formed IncidentAlert. Returns immediately… (+8 more)

### Community 18 - "command.tsx"
Cohesion: 0.20
Nodes (8): Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator, CommandShortcut()

### Community 19 - "menubar.tsx"
Cohesion: 0.12
Nodes (11): Menubar, MenubarCheckboxItem, MenubarContent, MenubarItem, MenubarLabel, MenubarRadioItem, MenubarSeparator, MenubarShortcut() (+3 more)

### Community 20 - "_print_rca"
Cohesion: 0.67
Nodes (3): _print_rca(), InvestigationResult, Print RCA to terminal in a readable format.

### Community 21 - "post"
Cohesion: 0.15
Nodes (17): create_runbook(), _forward_camunda_post(), proxy_camunda_incident_resolution(), proxy_camunda_incidents(), proxy_camunda_process_definitions(), proxy_camunda_process_instances(), proxy_camunda_variables(), Helper to forward POST requests to Camunda 8.9 REST API. (+9 more)

### Community 22 - "cn"
Cohesion: 0.17
Nodes (17): ButtonProps, buttonVariants, Calendar(), CalendarDayButton(), DropdownMenuShortcut(), Pagination(), PaginationContent, PaginationEllipsis() (+9 more)

### Community 23 - "main.py"
Cohesion: 0.13
Nodes (19): delete, _check_sb_cached(), delete_runbook(), get_runbooks(), health(), list_investigations(), list_runbooks(), proxy_camunda_process_definition_xml() (+11 more)

### Community 24 - "dependencies"
Cohesion: 0.15
Nodes (13): dependencies, input-otp, @radix-ui/react-checkbox, @radix-ui/react-navigation-menu, @radix-ui/react-radio-group, recharts, @tanstack/router-plugin, input-otp (+5 more)

### Community 25 - "watcher.py"
Cohesion: 0.22
Nodes (11): FileCreatedEvent, FileSystemEventHandler, IncidentHandler, main(), Path, watcher.py — Graphify Auto-trigger File Watcher…, Triggers an RCA investigation whenever a new JSON file appears., Run opensre investigate on the given file and display the RCA. (+3 more)

### Community 26 - "context-menu.tsx"
Cohesion: 0.20
Nodes (9): ContextMenuCheckboxItem, ContextMenuContent, ContextMenuItem, ContextMenuLabel, ContextMenuRadioItem, ContextMenuSeparator, ContextMenuShortcut(), ContextMenuSubContent (+1 more)

### Community 27 - "alert-dialog.tsx"
Cohesion: 0.22
Nodes (8): AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter(), AlertDialogHeader(), AlertDialogOverlay, AlertDialogTitle

### Community 28 - "table.tsx"
Cohesion: 0.12
Nodes (14): Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, Table, TableBody (+6 more)

### Community 29 - "breadcrumb.tsx"
Cohesion: 0.25
Nodes (7): Breadcrumb, BreadcrumbEllipsis(), BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator()

### Community 30 - "drawer.tsx"
Cohesion: 0.25
Nodes (6): DrawerContent, DrawerDescription, DrawerFooter(), DrawerHeader(), DrawerOverlay, DrawerTitle

### Community 31 - "navigation-menu.tsx"
Cohesion: 0.25
Nodes (7): NavigationMenu, NavigationMenuContent, NavigationMenuIndicator, NavigationMenuList, NavigationMenuTrigger, navigationMenuTriggerStyle, NavigationMenuViewport

### Community 32 - "worker.py"
Cohesion: 0.29
Nodes (5): _call_sentinel(), _print_rca_result(), camunda/worker.py — Camunda 8 Zeebe Job Worker (pyzeebe)…, POST to Sentinel /investigate/from-error and poll for result., Print the investigation result in clear What / Why / How format. This is shown…

### Community 33 - "OpenSRE + Camunda 8 + DGX AI Agent — Complete Documentation"
Cohesion: 0.07
Nodes (29): 1. Start Docker Infrastructure, 1. System Architecture, 2. Port & Service Map, 2. Start Real-Time SRE Bridge, 3.1 Software Requirements, 3.2 Python Dependencies, 3.3 DGX Server SSH Tunnel, 3. (Optional) Start Sentinel FastAPI API (+21 more)

### Community 34 - "toggle-group.tsx"
Cohesion: 0.33
Nodes (5): ToggleGroup, ToggleGroupContext, ToggleGroupItem, Toggle, toggleVariants

### Community 35 - "alert.tsx"
Cohesion: 0.40
Nodes (4): Alert, AlertDescription, AlertTitle, alertVariants

### Community 36 - "OpenSRE (Graphify) — Product Presentation & Demo Script"
Cohesion: 0.09
Nodes (21): 1. Executive Summary (The 30-Second Elevator Pitch), 2. The Real-World Problem We Solve, 3. How the System Works (In Plain English), 4. Complete Feature Breakdown & Implementation, 5. Step-by-Step Live Demo Script, 6. Architecture & Technical Highlights, 7. Business Value, Security & ROI for Clients, 8. Technical Glossary (Simplified Terms) (+13 more)

### Community 37 - "carousel.tsx"
Cohesion: 0.15
Nodes (12): Carousel, CarouselApi, CarouselContent, CarouselContext, CarouselContextProps, CarouselItem, CarouselNext, CarouselOptions (+4 more)

### Community 38 - "tabs.tsx"
Cohesion: 0.50
Nodes (3): TabsContent, TabsList, TabsTrigger

### Community 58 - "processes.tsx"
Cohesion: 0.27
Nodes (8): DialogContent, DialogDescription, DialogFooter(), DialogHeader(), DialogOverlay, DialogTitle, Input, ProcessesPage()

### Community 98 - "chart.tsx"
Cohesion: 0.20
Nodes (7): ChartConfig, ChartContainer, ChartContext, ChartContextProps, ChartLegendContent, ChartTooltipContent, THEMES

### Community 99 - "sheet.tsx"
Cohesion: 0.22
Nodes (8): SheetContent, SheetContentProps, SheetDescription, SheetFooter(), SheetHeader(), SheetOverlay, SheetTitle, sheetVariants

### Community 100 - "Graphify — Real-Time Camunda 8 SRE Incident Remediation"
Cohesion: 0.22
Nodes (8): Architecture Overview, Graphify — Real-Time Camunda 8 SRE Incident Remediation, How It Works, OpenSRE Commands Reference, Phase 1 — Test OpenSRE directly (no Docker needed), Phase 2 — Full stack (Camunda + Sentinel), Quick Start, Run Tests

### Community 101 - "react"
Cohesion: 0.25
Nodes (7): react, useCarousel(), useChart(), useFormField(), useSidebar(), useIsMobile(), react

### Community 102 - "OpenSRE Dashboard — AI SRE & Workflow Incident Management"
Cohesion: 0.33
Nodes (5): Behavior, Design direction, OpenSRE Dashboard — AI SRE & Workflow Incident Management, Pages, Technical notes

### Community 103 - "Welcome to your Lovable project"
Cohesion: 0.40
Nodes (4): Build with Lovable, Built with, Development, Welcome to your Lovable project

### Community 104 - "input-otp.tsx"
Cohesion: 0.40
Nodes (4): InputOTP, InputOTPGroup, InputOTPSeparator, InputOTPSlot

## Knowledge Gaps
- **367 isolated node(s):** `$schema`, `style`, `rsc`, `tsx`, `css` (+362 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **49 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `cn()` connect `cn` to `RcaDetail.tsx`, `form.tsx`, `sidebar.tsx`, `MetricCard.tsx`, `utils.ts`, `command.tsx`, `menubar.tsx`, `context-menu.tsx`, `alert-dialog.tsx`, `table.tsx`, `breadcrumb.tsx`, `drawer.tsx`, `navigation-menu.tsx`, `toggle-group.tsx`, `alert.tsx`, `carousel.tsx`, `tabs.tsx`, `processes.tsx`, `chart.tsx`, `sheet.tsx`, `input-otp.tsx`, `tooltip.tsx`?**
  _High betweenness centrality (0.194) - this node is a cross-community bridge._
- **Why does `dependencies` connect `dependencies` to `devDependencies`, `bpmn-js`, `class-variance-authority`, `clsx`, `cmdk`, `embla-carousel-react`, `@hookform/resolvers`, `lucide-react`, `@radix-ui/react-accordion`, `@radix-ui/react-alert-dialog`, `@radix-ui/react-aspect-ratio`, `@radix-ui/react-avatar`, `@radix-ui/react-collapsible`, `@radix-ui/react-context-menu`, `@radix-ui/react-dialog`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-hover-card`, `@radix-ui/react-label`, `@radix-ui/react-menubar`, `@radix-ui/react-popover`, `@radix-ui/react-progress`, `@radix-ui/react-scroll-area`, `@radix-ui/react-select`, `@radix-ui/react-separator`, `@radix-ui/react-slider`, `@radix-ui/react-slot`, `@radix-ui/react-switch`, `@radix-ui/react-tabs`, `@radix-ui/react-toggle`, `@radix-ui/react-toggle-group`, `@radix-ui/react-tooltip`, `react-day-picker`, `react-dom`, `react-hook-form`, `react-resizable-panels`, `sonner`, `tailwind-merge`, `tailwindcss`, `@tailwindcss/vite`, `@tanstack/react-query`, `@tanstack/react-router`, `@tanstack/react-start`, `tw-animate-css`, `vaul`, `vite-tsconfig-paths`, `zod`, `react`, `date-fns`?**
  _High betweenness centrality (0.175) - this node is a cross-community bridge._
- **Why does `react` connect `react` to `dependencies`, `cn`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **What connects `$schema`, `style`, `rsc` to the rest of the system?**
  _367 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `RcaDetail.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.050128708847039696 - nodes in this community are weakly interconnected._
- **Should `devDependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.04081632653061224 - nodes in this community are weakly interconnected._
- **Should `camunda_bridge.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07397959183673469 - nodes in this community are weakly interconnected._