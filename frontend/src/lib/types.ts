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

// M7 Slice 2B: backend enum, verbatim - never a fourth state, never
// translated here (see ExecutiveReasoningPanel for the localized display
// label mapping, which is presentation-only and never changes this value).
export type ReasoningState = "aligned" | "tension" | "insufficient_evidence";

// M8 Slice 4C-2: cited_organizational_memory reference NO internal OM#
// labels or durable ids - only an opaque, backend-assigned presentation id
// ("h1", "h2", ...) with no backend lookup semantics, matching the e#/c#
// convention above. Reuses OutcomeResultState (Slice 3C-2) verbatim - the
// backend's public item shape is the exact same enum.
export type OrganizationalMemoryOutcomeExplainability = {
  result_state: OutcomeResultState;
  summary: string;
  observed_at: string;
};

export type CitedOrganizationalMemoryItem = {
  id: string;
  decision: string;
  rationale: string | null;
  decided_at: string;
  outcomes: OrganizationalMemoryOutcomeExplainability[];
  omitted_outcomes_count: number;
};

export type Explainability = {
  cited_evidence: ExplainabilityEvidenceItem[];
  cited_company_basis: ExplainabilityCompanyBasisItem[];
  // M8 Slice 4C-2: a THIRD, distinct citation category - historical human
  // Decision/Outcome context, never merged with cited_evidence/
  // cited_company_basis. See app/services/explainability.py's
  // cited_organizational_memory for the closed backend contract.
  cited_organizational_memory: CitedOrganizationalMemoryItem[];
  confidence: ExplainabilityConfidence | null;
  // M7 Slice 2B: safe executive-provenance passthrough from the FINAL
  // accepted reasoning_assessment - see app/services/explainability.py.
  // Never reconstructed/inferred in frontend code.
  reasoning_state: ReasoningState | null;
  operational_assessment: string | null;
  // Verbatim controlled-vocabulary string from the backend (frozen UX
  // decision, Slice 2B Section 8) - never re-mapped to another label here.
  company_brain_alignment: string | null;
  tensions: string[];
  evidence_gaps: string[];
  risk_assessment: string | null;
  // Structured, server-resolved gap provenance - same safe shape as
  // cited_evidence (see app/services/explainability.py's
  // _resolve_missing_evidence, which reuses _sanitize_evidence_item).
  missing_evidence: ExplainabilityEvidenceItem[];
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
  // M8 Slice 3A: the immutable OME reasoning receipt id for this response
  // (null only for internal/test construction that predates live receipt
  // creation - a real successful /ai/chat response always sets it). This
  // is the RAW backend field only - never confuse with the frontend-local
  // recordedDecisionId annotation on PersistedChatMeta below, which the
  // backend never returns.
  reasoning_receipt_id: string | null;
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
  // M8 Slice 3B-2: safe opaque UUID annotations only - never a policy,
  // provenance catalog, or free-text field. reasoning_receipt_id is
  // copied verbatim from the live ChatMeta field above.
  // recorded_decision_id is FRONTEND-LOCAL ONLY - the backend /ai/chat
  // response never returns it; it is set here only after a successful,
  // separate POST /decisions call (see components/chat/RecordDecision.tsx)
  // and stays null until then. Founder Correction 1 (M8 Slice 3B-2): this
  // is deliberately NOT part of raw ChatMeta above, so the raw backend
  // response type never blurs with frontend-local UI state.
  reasoning_receipt_id: string | null;
  recorded_decision_id: string | null;
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

// M8 Slice 3B-2: mirrors the closed backend contract
// (app/api/decisions.py) exactly - no field beyond these four is ever
// client-authorable. company_id/created_by_user_id/status/timestamps/
// provenance/supersession fields are never part of this type.
export type DecisionCreateRequest = {
  reasoning_receipt_id: string;
  decision_text: string;
  rationale: string | null;
  situation_id: string | null;
};

export type DecisionResponse = {
  id: string;
  reasoning_receipt_id: string;
  situation_id: string | null;
  decision_text: string;
  rationale: string | null;
  status: string;
  decided_at: string;
  created_at: string;
};

// M8 Slice 3C-2: mirrors the closed backend contract (app/api/outcomes.py)
// exactly - no field beyond these four is ever client-authorable.
// company_id/recorded_by_user_id/status/created_at/evidence/provenance/
// supersession fields are never part of this type.
export type OutcomeResultState = "positive" | "negative" | "mixed" | "unknown";

export type OutcomeCreateRequest = {
  decision_memory_id: string;
  outcome_summary: string;
  result_state: OutcomeResultState;
  observed_at?: string;
};

export type OutcomeResponse = {
  id: string;
  decision_memory_id: string;
  outcome_summary: string;
  result_state: OutcomeResultState;
  status: string;
  observed_at: string;
  created_at: string;
};
