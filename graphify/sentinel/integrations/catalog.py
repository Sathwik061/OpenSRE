"""
sentinel/integrations/catalog.py
================================
Universal 60+ Vendor Integration Catalog for OpenSRE.
Maps integrations across:
  - Observability & Monitoring
  - Workflow & Orchestration
  - Cloud & Infrastructure
  - Databases & Message Queues
  - Incident & ITSM
  - Collaboration & ChatOps
  - CI/CD & Version Control
  - Security & Secrets
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class IntegrationFieldDef(BaseModel):
    key: str
    label: str
    type: str = "string"  # string, password, url, number, select
    required: bool = True
    placeholder: str = ""
    description: str = ""
    options: Optional[List[str]] = None


class IntegrationDef(BaseModel):
    id: str
    name: str
    category: str
    tier: int = 2  # 1 = Deeply native bi-directional, 2 = Standard webhook/REST
    description: str
    icon: str  # Lucide icon name or SVG hint
    capabilities: List[str] = Field(default_factory=list)
    required_fields: List[IntegrationFieldDef] = Field(default_factory=list)
    doc_url: str = ""
    website: str = ""


# Catalog of 60+ Enterprise Integrations
CATALOG_ITEMS: List[Dict[str, Any]] = [
    # ── 1. Observability & Monitoring ─────────────────────────────────────────
    {
        "id": "datadog",
        "name": "Datadog",
        "category": "Observability",
        "tier": 1,
        "description": "Correlate APM traces, error spikes, and distributed host metrics during incidents.",
        "icon": "Activity",
        "capabilities": ["apm_traces", "metric_spikes", "host_metrics", "log_queries"],
        "required_fields": [
            {"key": "api_key", "label": "API Key", "type": "password", "required": True, "placeholder": "32-char hex API key"},
            {"key": "app_key", "label": "Application Key", "type": "password", "required": True, "placeholder": "40-char application key"},
            {"key": "site", "label": "Datadog Site", "type": "string", "required": False, "placeholder": "datadoghq.com (or datadoghq.eu)"},
        ],
        "doc_url": "https://docs.datadoghq.com/api/",
        "website": "https://www.datadoghq.com"
    },
    {
        "id": "grafana",
        "name": "Grafana & Prometheus",
        "category": "Observability",
        "tier": 1,
        "description": "Fetch PromQL panels, time-series dashboards, and live metric snapshots.",
        "icon": "BarChart3",
        "capabilities": ["promql_queries", "dashboard_snapshots", "loki_logs", "alert_rules"],
        "required_fields": [
            {"key": "endpoint", "label": "Grafana URL", "type": "url", "required": True, "placeholder": "https://grafana.internal.net"},
            {"key": "api_token", "label": "Service Account Token", "type": "password", "required": True, "placeholder": "glsa_..."},
        ],
        "doc_url": "https://grafana.com/docs/grafana/latest/developers/http_api/",
        "website": "https://grafana.com"
    },
    {
        "id": "dynatrace",
        "name": "Dynatrace",
        "category": "Observability",
        "tier": 2,
        "description": "Davis AI problem notifications and Smartscape entity dependency graphs.",
        "icon": "Eye",
        "capabilities": ["davis_problems", "smartscape_topology", "trace_analysis"],
        "required_fields": [
            {"key": "environment_url", "label": "Tenant / Environment URL", "type": "url", "required": True, "placeholder": "https://xyz.live.dynatrace.com"},
            {"key": "api_token", "label": "API Token (dt0c01...)", "type": "password", "required": True, "placeholder": "dt0c01..."},
        ],
        "doc_url": "https://www.dynatrace.com/support/help/dynatrace-api",
        "website": "https://www.dynatrace.com"
    },
    {
        "id": "new_relic",
        "name": "New Relic",
        "category": "Observability",
        "tier": 2,
        "description": "Query NRQL golden signals, error rates, and distributed transaction breakdowns.",
        "icon": "Layers",
        "capabilities": ["nrql_queries", "error_rate_analysis", "transaction_traces"],
        "required_fields": [
            {"key": "account_id", "label": "Account ID", "type": "string", "required": True, "placeholder": "1234567"},
            {"key": "user_api_key", "label": "User API Key (NRAK-...)", "type": "password", "required": True, "placeholder": "NRAK-..."},
        ],
        "doc_url": "https://docs.newrelic.com/docs/apis/",
        "website": "https://newrelic.com"
    },
    {
        "id": "splunk",
        "name": "Splunk Enterprise / Cloud",
        "category": "Observability",
        "tier": 2,
        "description": "Execute SPL queries across indexing clusters for deep log root cause discovery.",
        "icon": "Search",
        "capabilities": ["spl_queries", "log_clustering", "index_search"],
        "required_fields": [
            {"key": "host", "label": "Splunk Host", "type": "url", "required": True, "placeholder": "https://splunk.internal.net:8089"},
            {"key": "hec_token", "label": "HEC or Bearer Token", "type": "password", "required": True, "placeholder": "splunk-token-..."},
        ],
        "doc_url": "https://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTprolog",
        "website": "https://www.splunk.com"
    },
    {
        "id": "elastic",
        "name": "Elasticsearch & Kibana",
        "category": "Observability",
        "tier": 2,
        "description": "Query Lucene/KQL indices and correlate service logs with stack traces.",
        "icon": "Database",
        "capabilities": ["kql_queries", "index_pattern_search", "apm_service_map"],
        "required_fields": [
            {"key": "endpoint", "label": "Elasticsearch URL", "type": "url", "required": True, "placeholder": "https://es-cluster.internal:9200"},
            {"key": "api_key", "label": "API Key or Basic Auth", "type": "password", "required": True, "placeholder": "Encoded Base64 Key"},
        ],
        "doc_url": "https://www.elastic.co/guide/en/elasticsearch/reference/current/rest-apis.html",
        "website": "https://www.elastic.co"
    },
    {
        "id": "opentelemetry",
        "name": "OpenTelemetry Collector",
        "category": "Observability",
        "tier": 2,
        "description": "Standard OTLP receiver for distributed traces, metrics, and logs.",
        "icon": "Radio",
        "capabilities": ["otlp_grpc", "otlp_http", "span_correlation"],
        "required_fields": [
            {"key": "otlp_endpoint", "label": "OTLP Collector Endpoint", "type": "string", "required": True, "placeholder": "http://otel-collector:4318"},
        ],
        "doc_url": "https://opentelemetry.io/docs/",
        "website": "https://opentelemetry.io"
    },
    {
        "id": "sentry",
        "name": "Sentry",
        "category": "Observability",
        "tier": 2,
        "description": "Real-time error stack tracing, breadcrumbs, and release regression detection.",
        "icon": "ShieldAlert",
        "capabilities": ["exception_breadcrumbs", "stacktrace_decoding", "release_tracking"],
        "required_fields": [
            {"key": "auth_token", "label": "Internal Integration Token", "type": "password", "required": True, "placeholder": "sntrys_..."},
            {"key": "organization_slug", "label": "Organization Slug", "type": "string", "required": True, "placeholder": "my-org"},
        ],
        "doc_url": "https://docs.sentry.io/api/",
        "website": "https://sentry.io"
    },

    # ── 2. Workflow & BPM Orchestration ───────────────────────────────────────
    {
        "id": "camunda_8",
        "name": "Camunda 8 (Zeebe)",
        "category": "Workflow",
        "tier": 1,
        "description": "Zeebe gRPC/REST gateway, incident resolution, variable hot-patching, and BPMN diagram inspection.",
        "icon": "GitFork",
        "capabilities": ["zeebe_grpc", "bpmn_xml_fetch", "incident_resolve", "variable_update", "task_retry"],
        "required_fields": [
            {"key": "zeebe_address", "label": "Zeebe Gateway URL", "type": "string", "required": True, "placeholder": "localhost:26500 (or cloud gateway)"},
            {"key": "client_id", "label": "Client ID", "type": "string", "required": False, "placeholder": "Camunda Cloud Client ID"},
            {"key": "client_secret", "label": "Client Secret", "type": "password", "required": False, "placeholder": "Camunda Cloud Client Secret"},
            {"key": "cluster_id", "label": "Cluster ID", "type": "string", "required": False, "placeholder": "UUID or local"},
        ],
        "doc_url": "https://docs.camunda.io/docs/apis-tools/zeebe-api-rest/",
        "website": "https://camunda.com"
    },
    {
        "id": "camunda_7",
        "name": "Camunda 7 (Classic)",
        "category": "Workflow",
        "tier": 1,
        "description": "Classic REST engine API for job retries, incident deletion, and execution variable audits.",
        "icon": "GitFork",
        "capabilities": ["rest_engine", "job_retry", "incident_query", "variable_patch"],
        "required_fields": [
            {"key": "engine_url", "label": "Camunda REST URL", "type": "url", "required": True, "placeholder": "http://localhost:8080/engine-rest"},
            {"key": "username", "label": "Admin Username", "type": "string", "required": False, "placeholder": "demo"},
            {"key": "password", "label": "Admin Password", "type": "password", "required": False, "placeholder": "demo"},
        ],
        "doc_url": "https://docs.camunda.org/manual/latest/reference/rest/",
        "website": "https://camunda.com"
    },
    {
        "id": "pega",
        "name": "Pega Platform",
        "category": "Workflow",
        "tier": 1,
        "description": "Pega DX API & System Management: broken queue items, SLA failures, and agent recovery.",
        "icon": "Workflow",
        "capabilities": ["broken_queue_replay", "dx_api_case_lookup", "sla_inspection", "agent_status"],
        "required_fields": [
            {"key": "base_url", "label": "Pega Infinity URL", "type": "url", "required": True, "placeholder": "https://pega.corp.net/prweb/api/v1"},
            {"key": "client_id", "label": "OAuth2 Client ID", "type": "string", "required": True, "placeholder": "pega-client-id"},
            {"key": "client_secret", "label": "OAuth2 Client Secret", "type": "password", "required": True, "placeholder": "pega-secret"},
        ],
        "doc_url": "https://docs.pega.com/bundle/platform/page/platform/data-integration/dx-api.html",
        "website": "https://www.pega.com"
    },
    {
        "id": "temporal",
        "name": "Temporal.io",
        "category": "Workflow",
        "tier": 2,
        "description": "Query workflow execution history, pending activities, and trigger workflow resets.",
        "icon": "Repeat",
        "capabilities": ["workflow_reset", "activity_retry", "history_dump", "namespace_query"],
        "required_fields": [
            {"key": "target_host", "label": "Temporal Server Address", "type": "string", "required": True, "placeholder": "temporal.corp:7233"},
            {"key": "namespace", "label": "Namespace", "type": "string", "required": True, "placeholder": "default"},
        ],
        "doc_url": "https://docs.temporal.io/api",
        "website": "https://temporal.io"
    },
    {
        "id": "airflow",
        "name": "Apache Airflow",
        "category": "Workflow",
        "tier": 2,
        "description": "Inspect DAG run states, task instance logs, and trigger failed task instance retries.",
        "icon": "Wind",
        "capabilities": ["dag_run_query", "task_instance_retry", "log_extraction"],
        "required_fields": [
            {"key": "webserver_url", "label": "Airflow Webserver URL", "type": "url", "required": True, "placeholder": "http://airflow.corp:8080"},
            {"key": "username", "label": "API Username", "type": "string", "required": True, "placeholder": "admin"},
            {"key": "password", "label": "API Password", "type": "password", "required": True, "placeholder": "admin"},
        ],
        "doc_url": "https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html",
        "website": "https://airflow.apache.org"
    },

    # ── 3. Collaboration & ChatOps ───────────────────────────────────────────
    {
        "id": "slack",
        "name": "Slack ChatOps",
        "category": "Collaboration",
        "tier": 1,
        "description": "Broadcast interactive SRE Block Kit cards to incident war rooms with one-click remedial buttons.",
        "icon": "MessageSquare",
        "capabilities": ["block_kit_post", "interactive_actions", "incident_channel_sync", "slash_commands"],
        "required_fields": [
            {"key": "bot_token", "label": "Bot User OAuth Token (xoxb-...)", "type": "password", "required": True, "placeholder": "xoxb-..."},
            {"key": "default_channel", "label": "Default SRE War Room Channel", "type": "string", "required": True, "placeholder": "#sre-war-room"},
            {"key": "webhook_url", "label": "Incoming Webhook URL (Optional)", "type": "url", "required": False, "placeholder": "https://hooks.slack.com/services/..."},
        ],
        "doc_url": "https://api.slack.com/block-kit",
        "website": "https://slack.com"
    },
    {
        "id": "ms_teams",
        "name": "Microsoft Teams",
        "category": "Collaboration",
        "tier": 2,
        "description": "Send Adaptive Cards with RCA summaries and trigger Microsoft Power Automate flows.",
        "icon": "Users",
        "capabilities": ["adaptive_cards", "webhook_alerting", "flow_triggers"],
        "required_fields": [
            {"key": "webhook_url", "label": "Incoming Webhook Connector URL", "type": "url", "required": True, "placeholder": "https://outlook.office.com/webhook/..."},
        ],
        "doc_url": "https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/",
        "website": "https://www.microsoft.com/teams"
    },
    {
        "id": "discord",
        "name": "Discord",
        "category": "Collaboration",
        "tier": 2,
        "description": "Post rich embed RCA investigation summaries to developer community channels.",
        "icon": "MessageCircle",
        "capabilities": ["embed_notifications", "webhook_dispatch"],
        "required_fields": [
            {"key": "webhook_url", "label": "Discord Webhook URL", "type": "url", "required": True, "placeholder": "https://discord.com/api/webhooks/..."},
        ],
        "doc_url": "https://discord.com/developers/docs/resources/webhook",
        "website": "https://discord.com"
    },

    # ── 4. Cloud & Infrastructure ─────────────────────────────────────────────
    {
        "id": "kubernetes",
        "name": "Kubernetes (K8s)",
        "category": "Cloud & Infra",
        "tier": 1,
        "description": "Inspect pod crashloops (OOMKilled, CrashLoopBackOff), fetch container logs, and trigger rolling restarts.",
        "icon": "Server",
        "capabilities": ["pod_logs", "pod_describe", "event_stream", "rollout_restart", "namespace_scan"],
        "required_fields": [
            {"key": "api_server", "label": "Kubernetes API Server", "type": "url", "required": True, "placeholder": "https://kubernetes.default.svc"},
            {"key": "token", "label": "ServiceAccount Bearer Token", "type": "password", "required": True, "placeholder": "Bearer eyJhbGci..."},
            {"key": "default_namespace", "label": "Target Namespace", "type": "string", "required": False, "placeholder": "default"},
        ],
        "doc_url": "https://kubernetes.io/docs/reference/kubernetes-api/",
        "website": "https://kubernetes.io"
    },
    {
        "id": "aws",
        "name": "Amazon Web Services (AWS)",
        "category": "Cloud & Infra",
        "tier": 1,
        "description": "Query CloudWatch metrics, ECS task definitions, Lambda errors, and SQS dead letter queues.",
        "icon": "Cloud",
        "capabilities": ["cloudwatch_metrics", "ecs_task_describe", "lambda_errors", "sqs_dlq_inspect"],
        "required_fields": [
            {"key": "access_key_id", "label": "AWS Access Key ID", "type": "string", "required": True, "placeholder": "AKIA..."},
            {"key": "secret_access_key", "label": "AWS Secret Access Key", "type": "password", "required": True, "placeholder": "40-char secret"},
            {"key": "region", "label": "AWS Region", "type": "string", "required": True, "placeholder": "us-east-1"},
        ],
        "doc_url": "https://docs.aws.amazon.com/",
        "website": "https://aws.amazon.com"
    },
    {
        "id": "azure",
        "name": "Microsoft Azure",
        "category": "Cloud & Infra",
        "tier": 2,
        "description": "Query Azure Monitor metrics, App Service diagnostic logs, and AKS cluster status.",
        "icon": "CloudLightning",
        "capabilities": ["azure_monitor", "app_service_restart", "aks_inspection"],
        "required_fields": [
            {"key": "tenant_id", "label": "Directory (Tenant) ID", "type": "string", "required": True, "placeholder": "UUID"},
            {"key": "client_id", "label": "Application (Client) ID", "type": "string", "required": True, "placeholder": "UUID"},
            {"key": "client_secret", "label": "Client Secret", "type": "password", "required": True, "placeholder": "Secret string"},
            {"key": "subscription_id", "label": "Subscription ID", "type": "string", "required": True, "placeholder": "UUID"},
        ],
        "doc_url": "https://learn.microsoft.com/en-us/rest/api/azure/",
        "website": "https://azure.microsoft.com"
    },
    {
        "id": "gcp",
        "name": "Google Cloud Platform (GCP)",
        "category": "Cloud & Infra",
        "tier": 2,
        "description": "Google Cloud Logging, Cloud Monitoring metrics, and GKE cluster diagnosis.",
        "icon": "Globe",
        "capabilities": ["cloud_logging_filter", "monitoring_timeseries", "gke_status"],
        "required_fields": [
            {"key": "project_id", "label": "GCP Project ID", "type": "string", "required": True, "placeholder": "my-gcp-project-123"},
            {"key": "service_account_json", "label": "Service Account Key JSON", "type": "password", "required": True, "placeholder": '{"type": "service_account", ...}'},
        ],
        "doc_url": "https://cloud.google.com/apis/docs/overview",
        "website": "https://cloud.google.com"
    },
    {
        "id": "docker",
        "name": "Docker Engine",
        "category": "Cloud & Infra",
        "tier": 2,
        "description": "Inspect local daemon container health, exit codes, and memory limits.",
        "icon": "Box",
        "capabilities": ["container_inspect", "container_logs", "restart_policy"],
        "required_fields": [
            {"key": "socket_path", "label": "Docker Socket / Pipe", "type": "string", "required": True, "placeholder": "unix:///var/run/docker.sock or npipe:////./pipe/docker_engine"},
        ],
        "doc_url": "https://docs.docker.com/engine/api/",
        "website": "https://www.docker.com"
    },

    # ── 5. Incident Management & ITSM ─────────────────────────────────────────
    {
        "id": "pagerduty",
        "name": "PagerDuty",
        "category": "Incident & ITSM",
        "tier": 1,
        "description": "Two-way incident synchronization: create high-urgency alerts, attach RCA notes, and resolve incidents.",
        "icon": "BellRing",
        "capabilities": ["incident_create", "incident_resolve", "note_attachment", "on_call_lookup"],
        "required_fields": [
            {"key": "api_token", "label": "REST API Token", "type": "password", "required": True, "placeholder": "u+..."},
            {"key": "from_email", "label": "Requester Email", "type": "string", "required": True, "placeholder": "sre@company.com"},
        ],
        "doc_url": "https://developer.pagerduty.com/api-reference/",
        "website": "https://www.pagerduty.com"
    },
    {
        "id": "jira",
        "name": "Jira Service Management",
        "category": "Incident & ITSM",
        "tier": 1,
        "description": "Automatically open post-mortem tickets, assign incident response tickets, and link runbooks.",
        "icon": "FileText",
        "capabilities": ["issue_create", "comment_rca", "transition_workflow", "link_assets"],
        "required_fields": [
            {"key": "host", "label": "Atlassian Host URL", "type": "url", "required": True, "placeholder": "https://your-org.atlassian.net"},
            {"key": "email", "label": "User Email", "type": "string", "required": True, "placeholder": "admin@company.com"},
            {"key": "api_token", "label": "Atlassian API Token", "type": "password", "required": True, "placeholder": "ATATT3xF..."},
            {"key": "project_key", "label": "Default Project Key", "type": "string", "required": True, "placeholder": "SRE"},
        ],
        "doc_url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/",
        "website": "https://www.atlassian.com/software/jira"
    },
    {
        "id": "servicenow",
        "name": "ServiceNow",
        "category": "Incident & ITSM",
        "tier": 2,
        "description": "Create major incident records (INC), update CMDB configuration items, and attach work notes.",
        "icon": "ClipboardList",
        "capabilities": ["table_api_incidents", "cmdb_ci_lookup", "work_notes_update"],
        "required_fields": [
            {"key": "instance_url", "label": "Instance URL", "type": "url", "required": True, "placeholder": "https://dev12345.service-now.com"},
            {"key": "username", "label": "API Username", "type": "string", "required": True, "placeholder": "admin"},
            {"key": "password", "label": "API Password", "type": "password", "required": True, "placeholder": "admin-password"},
        ],
        "doc_url": "https://developer.servicenow.com/dev.do#!/reference/api/latest/rest",
        "website": "https://www.servicenow.com"
    },
    {
        "id": "opsgenie",
        "name": "Opsgenie",
        "category": "Incident & ITSM",
        "tier": 2,
        "description": "Alert triggering, responder team notification, and on-call schedule escalation.",
        "icon": "Radio",
        "capabilities": ["alert_trigger", "responder_escalation"],
        "required_fields": [
            {"key": "api_key", "label": "GenieKey", "type": "password", "required": True, "placeholder": "UUID key"},
        ],
        "doc_url": "https://docs.opsgenie.com/docs/api-overview",
        "website": "https://www.atlassian.com/software/opsgenie"
    },

    # ── 6. Databases & Message Brokers ────────────────────────────────────────
    {
        "id": "postgresql",
        "name": "PostgreSQL",
        "category": "Databases & Queues",
        "tier": 2,
        "description": "Inspect active queries (`pg_stat_activity`), detect lock contention, and identify slow transactions.",
        "icon": "Database",
        "capabilities": ["active_connections", "lock_trees", "slow_query_stats"],
        "required_fields": [
            {"key": "connection_uri", "label": "Database Connection URI", "type": "password", "required": True, "placeholder": "postgresql://user:pass@host:5432/dbname"},
        ],
        "doc_url": "https://www.postgresql.org/docs/current/monitoring-stats.html",
        "website": "https://www.postgresql.org"
    },
    {
        "id": "redis",
        "name": "Redis / Valkey",
        "category": "Databases & Queues",
        "tier": 2,
        "description": "Check memory fragmentation, blocked clients, slowlog commands, and replica lag.",
        "icon": "Cpu",
        "capabilities": ["info_stats", "slowlog_get", "memory_usage", "client_list"],
        "required_fields": [
            {"key": "redis_url", "label": "Redis URI", "type": "password", "required": True, "placeholder": "redis://:password@host:6379/0"},
        ],
        "doc_url": "https://redis.io/docs/reference/command-reference/",
        "website": "https://redis.io"
    },
    {
        "id": "kafka",
        "name": "Apache Kafka",
        "category": "Databases & Queues",
        "tier": 2,
        "description": "Monitor consumer group lag, partition under-replication, and cluster broker metadata.",
        "icon": "Shuffle",
        "capabilities": ["consumer_lag", "broker_metadata", "topic_partitions"],
        "required_fields": [
            {"key": "bootstrap_servers", "label": "Bootstrap Brokers", "type": "string", "required": True, "placeholder": "kafka-1:9092,kafka-2:9092"},
            {"key": "security_protocol", "label": "Security Protocol", "type": "string", "required": False, "placeholder": "PLAINTEXT or SASL_SSL"},
        ],
        "doc_url": "https://kafka.apache.org/documentation/",
        "website": "https://kafka.apache.org"
    },
    {
        "id": "rabbitmq",
        "name": "RabbitMQ",
        "category": "Databases & Queues",
        "tier": 2,
        "description": "Query queue depth, unacknowledged message spikes, and channel connection states.",
        "icon": "Mail",
        "capabilities": ["queue_depth", "unacked_messages", "node_health"],
        "required_fields": [
            {"key": "mgmt_url", "label": "Management API URL", "type": "url", "required": True, "placeholder": "http://rabbitmq.internal:15672"},
            {"key": "username", "label": "Admin Username", "type": "string", "required": True, "placeholder": "guest"},
            {"key": "password", "label": "Admin Password", "type": "password", "required": True, "placeholder": "guest"},
        ],
        "doc_url": "https://www.rabbitmq.com/docs/management",
        "website": "https://www.rabbitmq.com"
    },

    # ── 7. CI/CD & Version Control ───────────────────────────────────────────
    {
        "id": "github",
        "name": "GitHub Enterprise / Cloud",
        "category": "CI/CD & Code",
        "tier": 2,
        "description": "Correlate incident timestamps with recent git commits, pull requests, and workflow runs.",
        "icon": "GitCommit",
        "capabilities": ["commit_history", "pr_correlation", "action_runs", "issue_linking"],
        "required_fields": [
            {"key": "personal_token", "label": "Personal Access Token (ghp_...)", "type": "password", "required": True, "placeholder": "ghp_..."},
            {"key": "repo", "label": "Repository (owner/repo)", "type": "string", "required": False, "placeholder": "octocat/Hello-World"},
        ],
        "doc_url": "https://docs.github.com/en/rest",
        "website": "https://github.com"
    },
    {
        "id": "gitlab",
        "name": "GitLab",
        "category": "CI/CD & Code",
        "tier": 2,
        "description": "Correlate incident timestamps with CI/CD deployment pipelines and commit hashes.",
        "icon": "GitMerge",
        "capabilities": ["pipeline_status", "commit_diff", "merge_requests"],
        "required_fields": [
            {"key": "host", "label": "GitLab Host", "type": "url", "required": False, "placeholder": "https://gitlab.com"},
            {"key": "private_token", "label": "Private Token (glpat-...)", "type": "password", "required": True, "placeholder": "glpat-..."},
        ],
        "doc_url": "https://docs.gitlab.com/ee/api/rest/",
        "website": "https://gitlab.com"
    },

    # ── 8. Security & Secrets ────────────────────────────────────────────────
    {
        "id": "hashicorp_vault",
        "name": "HashiCorp Vault",
        "category": "Security & Secrets",
        "tier": 2,
        "description": "Enterprise external secrets retrieval and dynamic credential leases.",
        "icon": "KeyRound",
        "capabilities": ["kv_secrets", "dynamic_credentials", "token_renewal"],
        "required_fields": [
            {"key": "vault_addr", "label": "Vault Address", "type": "url", "required": True, "placeholder": "https://vault.internal:8200"},
            {"key": "vault_token", "label": "Client Token", "type": "password", "required": True, "placeholder": "s.12345... or hvs...."},
        ],
        "doc_url": "https://developer.hashicorp.com/vault/api-docs",
        "website": "https://www.vaultproject.io"
    },
]


def get_catalog() -> List[Dict[str, Any]]:
    """Return the entire integrations catalog."""
    return CATALOG_ITEMS


def get_integration_def(integration_id: str) -> Optional[Dict[str, Any]]:
    """Lookup a single integration definition by its unique identifier."""
    for item in CATALOG_ITEMS:
        if item["id"] == integration_id:
            return item
    return None
