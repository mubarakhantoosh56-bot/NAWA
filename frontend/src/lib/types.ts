export type Company = {
  id: string;
  slug: string;
  name: string;
  status: string;
  plan: string;
};

export type User = {
  id: string;
  email: string;
  full_name: string;
  status: string;
  auth_provider: string;
};

export type Membership = {
  id: string;
  company_id: string;
  user_id: string;
  role_id: string;
  department_id: string | null;
  status: string;
};

export type Role = {
  id: string;
  slug: string;
  name: string;
  permissions: string[];
  is_system_role: boolean;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  company: Company;
  user: User;
  membership: Membership;
};

export type MeResponse = {
  company: Company;
  user: User;
  membership: Membership;
  role: Role;
};

export type Department = {
  id: string;
  company_id: string;
  name: string;
  slug: string;
  description: string | null;
  department_type: string;
  ai_agent_enabled: boolean;
  ai_agent_config: Record<string, unknown>;
};

export type DepartmentListResponse = {
  departments: Department[];
};

export type CompanyIntelligenceProfile = {
  company_name: string;
  industry: string;
  business_type: string;
  country_market: string;
  company_size: string;
  departments_enabled: string[];
  primary_goals: string;
  current_operational_challenges: string;
  growth_priorities: string;
  preferred_response_language: "en" | "ar";
  is_active: boolean;
};

export type ChatRequest = {
  company_id: string;
  session_id: string;
  message: string;
  context?: Record<string, unknown>;
  department_id?: string;
};

// M7 Slice 2A: public explainability contract. cited_evidence/
// cited_company_basis reference NO internal T#/CB# ids - only opaque,
// backend-assigned presentation ids ("e1", "e2", "c1", ...) with no
// backend lookup semantics. Never reconstruct a T#/CB# from these ids or
// from array position - the backend already resolved and sanitized
// everything cited by the final accepted answer.
export type ExplainabilityEntity = {
  type: string | null;
  reference: string | null;
};

export type ExplainabilityEvidenceItem = {
  id: string;
  label: string | null;
  filename: string | null;
  report_date: string | null;
  entity: ExplainabilityEntity | null;
  epistemic_origin: string | null;
  source_time_status: string | null;
};

export type ExplainabilityCompanyBasisItem = {
  id: string;
  label: string | null;
  type: string | null;
  statement: string | null;
};

export type ConfidenceBand = "low" | "moderate" | "high";

export type ConfidenceDriver =
  | "missing_evidence"
  | "unresolved_source_time"
  | "conflicted_company_basis";

export type ExplainabilityConfidence = {
  value: number;
  band: ConfidenceBand;
  drivers: ConfidenceDriver[];
};

export type Explainability = {
  cited_evidence: ExplainabilityEvidenceItem[];
  cited_company_basis: ExplainabilityCompanyBasisItem[];
  confidence: ExplainabilityConfidence | null;
};

export type ChatDecisionContextDepartment = {
  key: string;
  name: string;
  type?: string;
  scope: string;
};

export type ChatDecisionContext = {
  department?: ChatDecisionContextDepartment;
  operational_events?: Record<string, string>[];
};

export type ChatBridgeStatus = {
  status: string;
} & Record<string, unknown>;

// M7 Slice 2A: explicit allowlist mirroring the backend's
// public_context_allowlist() (app/services/decision_context.py) - the ONLY
// fields the public chat response can ever contain. Do not widen this type
// to Record<string, unknown> again: that reopens the internal-context leak
// this slice closed (raw Decision Context, full Truth/Company Brain
// catalogs, reasoning_reference_catalog, internal UUID/path provenance).
export type ChatContext = {
  operational_events_bridge?: ChatBridgeStatus;
  truth_context_bridge?: ChatBridgeStatus;
  company_brain_bridge?: ChatBridgeStatus;
  company_intelligence_profile?: Partial<CompanyIntelligenceProfile> | null;
  decision_context?: ChatDecisionContext;
  explainability?: Explainability | null;
};

export type ChatMeta = {
  company_id: string | null;
  session_id: string | null;
  context: ChatContext;
  language?: "en" | "ar";
  parse_ok: boolean;
  memory_injected: boolean;
  events_count: number;
};

export type ChatResponse = {
  ceo_text: string;
  // M7 Slice 2A: intentionally `unknown`, not a structured type. logic_json
  // is internal M6 reasoning-engine output preserved for backend
  // compatibility only - new frontend code must not read fields off it
  // directly (that would require an unsafe cast, which is the point: use
  // meta.context.explainability instead). See Slice 2B for the
  // replacement Executive Reasoning UI that will consume explainability.
  logic_json: unknown;
  followup_question: string | null;
  meta: ChatMeta;
};

// M7 Slice 2A privacy contract (see frontend/src/components/chat/
// ChatPanel.tsx): the ONLY chat-turn shape ever written to or read from
// localStorage (nawa.chat.{companyId}). Never carries meta.context, raw
// Decision Context, Truth/Company Brain catalogs, internal UUID/path
// provenance, or logic_json - only what visible chat continuity needs.
export type PersistedChatMeta = {
  parse_ok: boolean;
  memory_injected: boolean;
  events_count: number;
  explainability: Explainability | null;
};

export type PersistedChatResponse = {
  ceo_text: string;
  followup_question: string | null;
  meta: PersistedChatMeta;
};

export type PersistedChatTurn = {
  id: string;
  userMessage: string;
  response: PersistedChatResponse;
};

// The in-memory/render type adds `logicJson` for the CURRENT session only
// - never read from or written to storage (a turn reloaded from a
// previous session simply has no logicJson; LogicPanel renders that as
// empty).
export type ChatTurn = PersistedChatTurn & {
  logicJson?: unknown;
};

export type CompanyFile = {
  id: string;
  company_id: string;
  department_id: string | null;
  uploaded_by_user_id: string;
  filename: string;
  content_type: string;
  file_size_bytes: number;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type FileListResponse = {
  files: CompanyFile[];
};

export type OperationalInputRequest = {
  department_id?: string | null;
  department_type?: string | null;
  target_department_id?: string | null;
  target_department_type?: string | null;
  category?: "daily_update" | "kpi" | "issue" | "decision" | "report" | "document" | "alert" | "note";
  priority?: "low" | "normal" | "watch" | "high" | "critical";
  event_date?: string | null;
  text?: string;
  metrics: Record<string, string>;
  files_attached?: Array<Record<string, string>>;
  payload?: Record<string, string>;
};

export type OperationalInputResponse = {
  status: string;
  event_type: string;
  department_id: string | null;
  department_type: string | null;
  target_department_id: string | null;
  category: string;
  priority: string;
  summary: string;
  memory_event_created: boolean;
  raw_input_id?: string | null;
  structured_record_draft_id?: string | null;
  classification?: Record<string, unknown> | null;
};

export type OperationalEventPriority = "low" | "normal" | "watch" | "high" | "critical";

export type OperationalEventCreateRequest = {
  company_id?: string | null;
  department_id?: string | null;
  event_type: string;
  category: string;
  priority: OperationalEventPriority;
  title: string;
  summary: string;
  event_timestamp?: string | null;
  source_type: string;
  source_ref?: string | null;
  payload: Record<string, unknown>;
  metadata: Record<string, unknown>;
};

export type OperationalEvent = {
  id: string;
  company_id: string;
  department_id: string | null;
  created_by_user_id: string;
  event_type: string;
  category: string;
  priority: OperationalEventPriority;
  title: string;
  summary: string;
  event_timestamp: string;
  source_type: string;
  source_ref: string | null;
  payload: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type OperationalEventListResponse = {
  events: OperationalEvent[];
};

export type OperationalSituation = {
  id: string;
  company_id: string;
  title: string;
  summary: string;
  situation_type: string;
  severity: string;
  status: string;
  time_window_start: string;
  time_window_end: string;
  department_id: string | null;
  detection_method: string;
  source_type: string;
  event_count: number;
  created_at: string;
  updated_at: string;
};

export type OperationalSituationListResponse = {
  situations: OperationalSituation[];
};

export type EventDraft = {
  id: string;
  company_id: string;
  file_id: string;
  department_id: string | null;
  proposed_title: string;
  proposed_category: string;
  proposed_priority: string;
  proposed_summary: string;
  evidence_quote: string | null;
  confidence: number;
  needs_clarification: boolean;
  clarification_hint: string | null;
  status: "pending" | "confirmed" | "rejected";
  confirmed_event_id: string | null;
  created_at: string;
  updated_at: string;
};

export type EventDraftListResponse = {
  file_id: string;
  drafts: EventDraft[];
};

export type DraftConfirmResponse = {
  draft: EventDraft;
  event: OperationalEvent;
};
