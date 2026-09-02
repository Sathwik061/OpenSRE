export type Severity = "critical" | "high" | "medium" | "low";
export type Environment = "production" | "staging" | "dev";
export type IncidentState = "ACTIVE" | "RESOLVED" | "SAVED_HISTORY";

export interface CamundaIncident {
  incidentKey: string;
  processDefinitionId: string;
  processInstanceKey: string;
  elementId: string;
  errorType: string;
  errorMessage: string;
  creationTime: string;
  state: string;
  rawIncidentKey?: string;
  rca?: RcaReport;
  rawOutput?: string;
}

export interface CamundaProcessInstance {
  processInstanceKey: string;
  processDefinitionId: string;
  processDefinitionVersion: number;
  state: string;
  hasIncident: boolean;
}

export interface CamundaProcessDefinition {
  processDefinitionKey: string;
  processDefinitionId: string;
  name: string;
  version: number;
}

export interface CamundaVariable {
  name: string;
  value: string;
  processInstanceKey?: string;
}

export interface RcaReport {
  summary: string;
  root_cause: string;
  confidence: string;
  observed_facts: string[];
  evidence: string[];
  recommended_actions: string[];
}

export interface InvestigationResult {
  status: string;
  incident: string;
  rca: RcaReport;
  raw_output?: string;
  incident_file?: string;
}

export interface InvestigatePayload {
  alert_name: string;
  service: string;
  environment: Environment;
  error: string;
  error_message: string;
  logs: string[];
  timeline: string[];
  severity: Severity;
  request?: string;
}

/** A single saved investigation record in localStorage. */
export interface HistoryRecord {
  id: string;
  savedAt: string;
  source: "camunda" | "ingest" | "template";
  title: string;
  service: string;
  environment: Environment;
  severity: Severity;
  errorType: string;
  errorMessage: string;
  resolutionStatus: "open" | "investigating" | "resolved";
  incidentKey?: string;
  processDefinitionId?: string;
  processInstanceKey?: string;
  rawIncidentKey?: string;
  elementId?: string;
  creationTime?: string;
  variables?: Record<string, string>;
  payload?: InvestigatePayload;
  rca?: RcaReport;
  rawOutput?: string;
  notes?: string;
  tags?: string[];
}

export interface IncidentCase {
  id: string;
  label: string;
  category: string;
  service: string;
  environment: Environment;
  severity: Severity;
  errorType: string;
  errorMessage: string;
  elementId: string;
  processDefinitionId: string;
  logs: string[];
  timeline: string[];
  variables: Record<string, string>;
}

export interface AppConfig {
  sentinelUrl: string;
  camundaUrl: string;
  dgxUrl: string;
  pollingIntervalMs: number;
  pollingEnabled: boolean;
  defaultStateFilter: IncidentState | "ALL";
}

export type ServiceStatus = "checking" | "online" | "offline";
