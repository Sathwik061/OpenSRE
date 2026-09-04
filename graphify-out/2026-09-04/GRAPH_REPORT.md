# Graph Report - .  (2026-09-04)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 942 nodes · 1581 edges · 98 communities (52 shown, 46 thin omitted)
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
- carousel.tsx
- sidebar.tsx
- routeTree.gen.ts
- incident_registry.py
- compilerOptions
- GraphifyHook
- LogFileTailer
- supabase_runbook.py
- test_sentinel.py
- cn
- utils.ts
- components.json
- server.ts
- run_investigation
- investigate_from_error
- command.tsx
- menubar.tsx
- _get
- post
- button.tsx
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
- card.tsx
- toggle-group.tsx
- alert.tsx
- accordion.tsx
- avatar.tsx
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
- @radix-ui/react-navigation-menu
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

## God Nodes (most connected - your core abstractions)
1. `cn()` - 88 edges
2. `compilerOptions` - 22 edges
3. `useApp()` - 19 edges
4. `run_bridge()` - 17 edges
5. `_get()` - 17 edges
6. `Button` - 12 edges
7. `saveHistoryRecord()` - 11 edges
8. `write()` - 10 edges
9. `downloadJson()` - 10 edges
10. `HistoryRecord` - 10 edges

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

## Communities (98 total, 46 thin omitted)

### Community 0 - "RcaDetail.tsx"
Cohesion: 0.05
Nodes (93): EmptyState(), OperateBpmnViewer(), OperateBpmnViewerProps, RcaDetail(), SeverityBadge(), StateChip(), styles, TypeChip() (+85 more)

### Community 1 - "devDependencies"
Cohesion: 0.04
Nodes (48): eslint, eslint-config-prettier, @eslint/js, eslint-plugin-prettier, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals, devDependencies (+40 more)

### Community 2 - "camunda_bridge.py"
Cohesion: 0.07
Nodes (43): build_incident_payload(), check_dgx_alive(), check_operate_alive(), fetch_bpmn_xml(), fetch_flow_node_name(), fetch_instance_variables(), fetch_live_incidents(), fetch_process_instance() (+35 more)

### Community 3 - "carousel.tsx"
Cohesion: 0.05
Nodes (36): react, Carousel, CarouselApi, CarouselContent, CarouselContext, CarouselContextProps, CarouselItem, CarouselNext (+28 more)

### Community 4 - "sidebar.tsx"
Cohesion: 0.06
Nodes (37): Separator, SheetContent, SheetContentProps, SheetDescription, SheetFooter(), SheetHeader(), SheetOverlay, SheetTitle (+29 more)

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
Cohesion: 0.14
Nodes (21): seed_predefined_runbooks.py — Seed Predefined Open SRE Runbooks into Supabase…, seed(), _bump_use_count(), delete_runbook(), _headers(), is_configured(), lookup_instance_rca(), lookup_sop_guidelines() (+13 more)

### Community 11 - "test_sentinel.py"
Cohesion: 0.11
Nodes (18): fixture, auth_error_event(), payment_incident(), tests/test_sentinel.py Smoke tests for the Sentinel FastAPI service. Run:…, Verify the response includes the path to the saved incident file., Verify the /investigate/from-error endpoint builds and investigates., Incomplete payload should return 422 Unprocessable Entity., Return current UTC timestamp in log format. (+10 more)

### Community 12 - "cn"
Cohesion: 0.15
Nodes (14): AppShell(), NAV, MetricCard(), useCountUp(), StatusDot(), StatusPill(), Badge(), BadgeProps (+6 more)

### Community 13 - "utils.ts"
Cohesion: 0.10
Nodes (12): Checkbox, HoverCardContent, InputOTP, InputOTPGroup, InputOTPSeparator, InputOTPSlot, PopoverContent, Progress (+4 more)

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
Cohesion: 0.12
Nodes (14): Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator, CommandShortcut() (+6 more)

### Community 19 - "menubar.tsx"
Cohesion: 0.12
Nodes (11): Menubar, MenubarCheckboxItem, MenubarContent, MenubarItem, MenubarLabel, MenubarRadioItem, MenubarSeparator, MenubarShortcut() (+3 more)

### Community 20 - "_get"
Cohesion: 0.12
Nodes (17): get_investigation(), list_investigations(), _print_rca(), proxy_camunda_process_definition_xml(), proxy_dgx_models(), InvestigationResult, Print RCA to terminal in a readable format., List all investigations this session with their status. (+9 more)

### Community 21 - "post"
Cohesion: 0.17
Nodes (16): create_runbook(), _forward_camunda_post(), proxy_camunda_incident_resolution(), proxy_camunda_incidents(), proxy_camunda_process_definitions(), proxy_camunda_process_instances(), proxy_camunda_variables(), Helper to forward POST requests to Camunda 8.9 REST API. (+8 more)

### Community 22 - "button.tsx"
Cohesion: 0.19
Nodes (12): ButtonProps, buttonVariants, Calendar(), CalendarDayButton(), Pagination(), PaginationContent, PaginationEllipsis(), PaginationItem (+4 more)

### Community 23 - "main.py"
Cohesion: 0.20
Nodes (13): delete, _check_sb_cached(), delete_runbook(), get_runbooks(), health(), list_runbooks(), Sentinel RCA Service — FastAPI application Receives error events (from Camunda…, Service liveness check — fast, non-blocking. (+5 more)

### Community 24 - "dependencies"
Cohesion: 0.15
Nodes (13): date-fns, dependencies, date-fns, input-otp, @radix-ui/react-checkbox, @radix-ui/react-radio-group, recharts, @tanstack/router-plugin (+5 more)

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
Cohesion: 0.22
Nodes (8): Table, TableBody, TableCaption, TableCell, TableFooter, TableHead, TableHeader, TableRow

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

### Community 33 - "card.tsx"
Cohesion: 0.29
Nodes (6): Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle

### Community 34 - "toggle-group.tsx"
Cohesion: 0.33
Nodes (5): ToggleGroup, ToggleGroupContext, ToggleGroupItem, Toggle, toggleVariants

### Community 35 - "alert.tsx"
Cohesion: 0.40
Nodes (4): Alert, AlertDescription, AlertTitle, alertVariants

### Community 36 - "accordion.tsx"
Cohesion: 0.50
Nodes (3): AccordionContent, AccordionItem, AccordionTrigger

### Community 37 - "avatar.tsx"
Cohesion: 0.50
Nodes (3): Avatar, AvatarFallback, AvatarImage

### Community 38 - "tabs.tsx"
Cohesion: 0.50
Nodes (3): TabsContent, TabsList, TabsTrigger

## Knowledge Gaps
- **314 isolated node(s):** `$schema`, `style`, `rsc`, `tsx`, `css` (+309 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **46 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `cn()` connect `cn` to `RcaDetail.tsx`, `carousel.tsx`, `sidebar.tsx`, `utils.ts`, `command.tsx`, `menubar.tsx`, `button.tsx`, `context-menu.tsx`, `alert-dialog.tsx`, `table.tsx`, `breadcrumb.tsx`, `drawer.tsx`, `navigation-menu.tsx`, `card.tsx`, `toggle-group.tsx`, `alert.tsx`, `accordion.tsx`, `avatar.tsx`, `tabs.tsx`?**
  _High betweenness centrality (0.208) - this node is a cross-community bridge._
- **Why does `dependencies` connect `dependencies` to `devDependencies`, `carousel.tsx`, `bpmn-js`, `class-variance-authority`, `clsx`, `cmdk`, `embla-carousel-react`, `@hookform/resolvers`, `lucide-react`, `@radix-ui/react-accordion`, `@radix-ui/react-alert-dialog`, `@radix-ui/react-aspect-ratio`, `@radix-ui/react-avatar`, `@radix-ui/react-collapsible`, `@radix-ui/react-context-menu`, `@radix-ui/react-dialog`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-hover-card`, `@radix-ui/react-label`, `@radix-ui/react-menubar`, `@radix-ui/react-navigation-menu`, `@radix-ui/react-popover`, `@radix-ui/react-progress`, `@radix-ui/react-scroll-area`, `@radix-ui/react-select`, `@radix-ui/react-separator`, `@radix-ui/react-slider`, `@radix-ui/react-slot`, `@radix-ui/react-switch`, `@radix-ui/react-tabs`, `@radix-ui/react-toggle`, `@radix-ui/react-toggle-group`, `@radix-ui/react-tooltip`, `react-day-picker`, `react-dom`, `react-hook-form`, `react-resizable-panels`, `sonner`, `tailwind-merge`, `tailwindcss`, `@tailwindcss/vite`, `@tanstack/react-query`, `@tanstack/react-router`, `@tanstack/react-start`, `tw-animate-css`, `vaul`, `vite-tsconfig-paths`, `zod`?**
  _High betweenness centrality (0.174) - this node is a cross-community bridge._
- **Why does `react` connect `carousel.tsx` to `dependencies`, `sidebar.tsx`, `button.tsx`?**
  _High betweenness centrality (0.153) - this node is a cross-community bridge._
- **What connects `$schema`, `style`, `rsc` to the rest of the system?**
  _314 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `RcaDetail.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.053268765133171914 - nodes in this community are weakly interconnected._
- **Should `devDependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.04081632653061224 - nodes in this community are weakly interconnected._
- **Should `camunda_bridge.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07397959183673469 - nodes in this community are weakly interconnected._