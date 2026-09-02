import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Maximize2,
  Minimize2,
  Minus,
  Plus,
  RotateCcw,
} from "lucide-react";
import Viewer from "bpmn-js/lib/NavigatedViewer";
import "bpmn-js/dist/assets/diagram-js.css";
import "bpmn-js/dist/assets/bpmn-font/css/bpmn.css";
import "bpmn-js/dist/assets/bpmn-js.css";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { camunda } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import { cn } from "@/lib/utils";

interface OperateBpmnViewerProps {
  processDefinitionKey?: string;
  processDefinitionId?: string;
  processInstanceKey?: string;
  elementId?: string;
  errorType?: string;
  errorMessage?: string;
  className?: string;
}

export function OperateBpmnViewer({
  processDefinitionKey,
  processDefinitionId,
  processInstanceKey,
  elementId,
  errorType,
  errorMessage,
  className,
}: OperateBpmnViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const { config } = useApp();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedElement, setSelectedElement] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [xmlContent, setXmlContent] = useState<string>("");

  // 1. Fetch BPMN XML when processDefinitionKey or processDefinitionId changes
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    async function loadXml() {
      try {
        let key = processDefinitionKey;
        // If no processDefinitionKey, search by processDefinitionId
        if (!key && processDefinitionId) {
          const defs = await camunda.searchProcessDefinitions(config.camundaUrl);
          const match = defs.find(
            (d) =>
              d.processDefinitionId === processDefinitionId ||
              d.name === processDefinitionId ||
              d.bpmnProcessId === processDefinitionId,
          );
          if (match) key = match.processDefinitionKey;
        }

        if (!key) {
          // Fallback: search any process definitions
          const defs = await camunda.searchProcessDefinitions(config.camundaUrl);
          if (defs.length > 0) {
            key = defs[0].processDefinitionKey;
          }
        }

        if (!key) {
          throw new Error("Process definition key not found");
        }

        const xml = await camunda.getProcessDefinitionXml(config.camundaUrl, key);
        if (!xml || xml.trim().length === 0) {
          throw new Error("Empty BPMN diagram returned from Camunda");
        }

        if (!cancelled) {
          setXmlContent(xml);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load BPMN diagram");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadXml();
    return () => {
      cancelled = true;
    };
  }, [processDefinitionKey, processDefinitionId, config.camundaUrl]);

  // 2. Render BPMN Canvas using bpmn-js
  useEffect(() => {
    if (!containerRef.current || !xmlContent) return;

    // Clean up previous viewer instance
    if (viewerRef.current) {
      try {
        viewerRef.current.destroy();
      } catch {
        /* ignore */
      }
      viewerRef.current = null;
    }

    const viewer = new Viewer({
      container: containerRef.current,
      keyboard: { bindTo: window },
    });
    viewerRef.current = viewer;

    viewer
      .importXML(xmlContent)
      .then(() => {
        const canvas = viewer.get("canvas");
        const overlays = viewer.get("overlays");
        const eventBus = viewer.get("eventBus");

        // Fit diagram smoothly into viewport
        canvas.zoom("fit-viewport", "auto");

        // Highlight failing element if elementId is provided
        if (elementId) {
          try {
            // Add red incident marker class
            canvas.addMarker(elementId, "bpmn-incident-marker");

            // Add Operate-style red incident badge overlay with count "1"
            const badgeEl = document.createElement("div");
            badgeEl.className = "bpmn-incident-badge";
            badgeEl.innerHTML = `
              <div class="bpmn-incident-pulse"></div>
              <span class="bpmn-incident-text">1</span>
            `;
            badgeEl.title = `Incident: ${errorType || "Error"} on ${elementId}\n${errorMessage || ""}`;

            overlays.add(elementId, "incident-badge", {
              position: { bottom: 10, right: 10 },
              html: badgeEl,
            });
          } catch (e) {
            console.warn("Could not mark element:", elementId, e);
          }
        }

        // Element click listener
        eventBus.on("element.click", (e: any) => {
          const el = e.element;
          if (el && el.id && !el.id.includes("_plane") && !el.id.includes("Process_")) {
            setSelectedElement(el.id);
          }
        });
      })
      .catch((err: any) => {
        console.error("BPMN render error:", err);
        setError("Failed to render BPMN visualization");
      });

    return () => {
      if (viewerRef.current) {
        try {
          viewerRef.current.destroy();
        } catch {
          /* ignore */
        }
        viewerRef.current = null;
      }
    };
  }, [xmlContent, elementId, errorType, errorMessage]);

  // Zoom controls
  function zoomIn() {
    viewerRef.current?.get("canvas")?.zoom("step", { factor: 1.25 });
  }

  function zoomOut() {
    viewerRef.current?.get("canvas")?.zoom("step", { factor: 0.8 });
  }

  function zoomReset() {
    viewerRef.current?.get("canvas")?.zoom("fit-viewport", "auto");
  }

  return (
    <div
      className={cn(
        "relative flex flex-col rounded-lg border-2 border-slate-300 bg-white text-slate-900 shadow-sm overflow-hidden transition-all duration-300 dark:border-slate-700 dark:bg-card dark:text-card-foreground",
        isFullscreen ? "fixed inset-0 z-50 h-screen w-screen rounded-none" : "h-[440px] w-full",
        className,
      )}
    >
      {/* Light Theme Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-slate-50/90 px-4 py-2.5 backdrop-blur-sm dark:border-slate-800 dark:bg-muted/40">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="flex size-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-semibold tracking-wide text-slate-800 dark:text-foreground">
              {processDefinitionId || "Process Model"}
            </span>
          </div>

          {processInstanceKey ? (
            <Badge variant="outline" className="border-slate-300 bg-white font-mono text-[11px] text-slate-700 dark:border-border dark:bg-background dark:text-foreground">
              Instance: {processInstanceKey}
            </Badge>
          ) : null}

          {elementId ? (
            <div className="flex items-center gap-1.5 rounded-full bg-red-50 px-2.5 py-0.5 border border-red-200 text-[11px] font-medium text-red-700 dark:bg-red-950/80 dark:border-red-800/60 dark:text-red-400">
              <span className="size-1.5 rounded-full bg-red-600 dark:bg-red-500" />
              Incident on: <code className="font-mono font-semibold text-red-800 dark:text-red-300">{elementId}</code>
            </div>
          ) : null}
        </div>

        {/* Viewport & Zoom Toolbar */}
        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant="ghost"
            className="size-7 p-0 text-slate-600 hover:bg-slate-200 hover:text-slate-900 dark:text-muted-foreground dark:hover:bg-muted dark:hover:text-foreground"
            onClick={zoomIn}
            title="Zoom In (+)"
          >
            <Plus className="size-3.5" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="size-7 p-0 text-slate-600 hover:bg-slate-200 hover:text-slate-900 dark:text-muted-foreground dark:hover:bg-muted dark:hover:text-foreground"
            onClick={zoomOut}
            title="Zoom Out (-)"
          >
            <Minus className="size-3.5" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="size-7 p-0 text-slate-600 hover:bg-slate-200 hover:text-slate-900 dark:text-muted-foreground dark:hover:bg-muted dark:hover:text-foreground"
            onClick={zoomReset}
            title="Fit to Viewport"
          >
            <RotateCcw className="size-3.5" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="size-7 p-0 text-slate-600 hover:bg-slate-200 hover:text-slate-900 dark:text-muted-foreground dark:hover:bg-muted dark:hover:text-foreground"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? <Minimize2 className="size-3.5" /> : <Maximize2 className="size-3.5" />}
          </Button>
        </div>
      </div>

      {/* BPMN Canvas Container */}
      <div className="relative flex-1 bg-white overflow-hidden">
        {loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-xs text-muted-foreground bg-white/90 z-10">
            <span className="size-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <span>Loading Camunda BPMN diagram...</span>
          </div>
        ) : error ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-4 text-center text-xs text-muted-foreground bg-white/90 z-10">
            <AlertCircle className="size-6 text-amber-500" />
            <p className="font-medium text-foreground">BPMN Diagram Unavailable</p>
            <p className="max-w-md text-muted-foreground">{error}</p>
          </div>
        ) : null}

        {/* bpmn-js Mounting Target */}
        <div ref={containerRef} className="size-full bpmn-operate-clean" />
      </div>

      {/* Embedded CSS for Clean Authentic BPMN Theme */}
      <style>{`
        .bpmn-operate-clean {
          background-color: #ffffff !important;
          background-image: radial-gradient(#e2e8f0 1px, transparent 1px) !important;
          background-size: 20px 20px !important;
        }
        .bpmn-operate-clean .djs-container svg {
          background-color: transparent !important;
        }

        /* BPMN.io Watermark displayed cleanly in bottom right */
        .bpmn-operate-clean .bjs-powered-by {
          display: block !important;
          opacity: 0.85 !important;
          position: absolute !important;
          bottom: 12px !important;
          right: 14px !important;
        }

        /* Red Incident Marker styling on failing element */
        .bpmn-incident-marker .djs-visual > rect,
        .bpmn-incident-marker .djs-visual > polygon,
        .bpmn-incident-marker .djs-visual > circle {
          stroke: #dc2626 !important;
          stroke-width: 3px !important;
          filter: drop-shadow(0 0 6px rgba(220, 38, 38, 0.45)) !important;
        }

        /* Floating Red Incident Badge */
        .bpmn-incident-badge {
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 22px;
          height: 22px;
          background-color: #dc2626;
          color: #ffffff;
          border-radius: 9999px;
          font-size: 11px;
          font-weight: 700;
          box-shadow: 0 2px 8px rgba(220, 38, 38, 0.5);
          cursor: pointer;
        }
        .bpmn-incident-pulse {
          position: absolute;
          inset: -4px;
          border-radius: 9999px;
          border: 2px solid #dc2626;
          animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
        @keyframes ping {
          75%, 100% {
            transform: scale(1.6);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
}
