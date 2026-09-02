-- ============================================================
--  Supabase Runbook Store for OpenSRE / Sentinel
--  Paste this into: Supabase Dashboard → SQL Editor → Run
-- ============================================================

-- Drop existing table if re-running
drop table if exists runbooks;

-- Main runbooks table
create table runbooks (
  id                  uuid          primary key default gen_random_uuid(),
  error_type          text          not null,
  process_id          text          not null default '*',
  summary             text          not null,
  root_cause          text          not null,
  recommended_actions jsonb         not null default '[]'::jsonb,
  observed_facts      jsonb         not null default '[]'::jsonb,
  confidence          text          not null default 'HIGH',
  source              text          not null default 'ai_generated',
  incident_key        text,
  instance_key        text,
  use_count           int           not null default 1,
  created_at          timestamptz   not null default now(),
  updated_at          timestamptz   not null default now()
);

-- Unique: one canonical runbook per (error_type, process_id) pair
create unique index idx_runbooks_unique on runbooks(error_type, process_id);
create index idx_runbooks_error_type on runbooks(error_type);

-- Auto-update updated_at on row change
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger runbooks_updated_at
  before update on runbooks
  for each row execute procedure update_updated_at();

-- Row Level Security — allow public read, anon write
alter table runbooks enable row level security;
create policy "Public read"  on runbooks for select using (true);
create policy "Anon write"   on runbooks for all    using (true) with check (true);

-- ============================================================
-- Seed with default runbooks for known Camunda error types
-- ============================================================
insert into runbooks (error_type, process_id, summary, root_cause, recommended_actions, observed_facts, confidence, source)
values
(
  'CONDITION_ERROR', '*',
  'BPMN sequence flow evaluation failed because no condition matched the input variables and no default flow was defined.',
  'The BPMN gateway has multiple outgoing sequence flows with conditions, but none evaluated to true given the current process variable state. No default flow was configured on the gateway to handle unmatched cases.',
  '["Review the BPMN model and identify the failing gateway.", "Inspect all outgoing sequence flow conditions from that gateway.", "Verify that at least one condition matches the expected variable values.", "Add null-checks or default values for optional variables.", "Add a default flow to the gateway to catch any unmatched cases.", "Test the process with the same variable payload in a local environment.", "Deploy the updated BPMN model and resolve the incident in Camunda Operate."]'::jsonb,
  '["Error type is CONDITION_ERROR", "A BPMN gateway has outgoing sequence flows with conditions", "No condition evaluated to true for the current variable state", "No default sequence flow is defined on the gateway"]'::jsonb,
  'HIGH', 'human_verified'
),
(
  'FORM_NOT_FOUND', '*',
  'A user task references a form that could not be found or is not deployed.',
  'The BPMN user task references a formId or formKey that does not exist in the Camunda form registry. This happens when the form was not deployed alongside the BPMN process or was deleted.',
  '["Check the user task in Camunda Modeler for the referenced formId or formKey.", "Verify the form exists in the form registry.", "Re-deploy the form using Camunda Modeler or REST API.", "Ensure the process version and form version are compatible.", "Retry the failed user task after deploying the correct form."]'::jsonb,
  '["Error type is FORM_NOT_FOUND", "A user task references a form not in the registry", "The process deployment may be incomplete"]'::jsonb,
  'HIGH', 'human_verified'
),
(
  'EXTRACT_VALUE_ERROR', '*',
  'A FEEL expression or variable extraction failed because the referenced variable is null or missing.',
  'A FEEL expression attempted to read a process variable that was null, undefined, or of an unexpected type. This occurs when upstream tasks failed to set a variable or when a variable name has a typo.',
  '["Identify the failing FEEL expression from the element ID in the incident.", "Check process variables at the point of failure.", "Verify all required input variables are set by upstream tasks.", "Add null-checks in FEEL expressions (e.g. if myVar != null then myVar else default).", "Correct any variable name typos in the process model.", "Re-deploy the updated process and retry."]'::jsonb,
  '["Error type is EXTRACT_VALUE_ERROR", "A FEEL expression evaluated against a null or missing variable", "Process variables may be incomplete or incorrectly named"]'::jsonb,
  'HIGH', 'human_verified'
),
(
  'IO_MAPPING_ERROR', '*',
  'Input/Output variable mapping between BPMN elements failed due to missing or incompatible variable types.',
  'The I/O mapping on a BPMN task could not map the source variable to the target. The source is null, does not exist, or has an incompatible type.',
  '["Check the I/O mapping configuration on the failing element in Camunda Modeler.", "Verify all source variables exist and have expected values.", "Ensure variable type compatibility between source and target.", "Add defensive checks or default values for nullable source variables.", "Re-deploy and retry the process instance."]'::jsonb,
  '["Error type is IO_MAPPING_ERROR", "Variable mapping between BPMN elements failed", "Source variable may be null or missing"]'::jsonb,
  'MEDIUM', 'human_verified'
)
on conflict (error_type, process_id) do nothing;

-- Verify seeded data
select error_type, process_id, confidence, source, created_at from runbooks order by created_at;
