import type { ChatResponse, CompanyFile, Department } from "@/lib/types";

export const DEMO_COMPANY = {
  name: "Jannat Al-Firdaws",
  slug: "jannat-al-firdaws",
  email: "owner@jannat-local.dev",
  role: "Owner",
};

export const DEMO_DEPARTMENTS: Department[] = [
  {
    id: "demo-production",
    company_id: "demo-company",
    name: "Production",
    slug: "production",
    description: "Production AI for output, downtime, wastage, and line issues.",
    department_type: "production_ai",
    ai_agent_enabled: true,
    ai_agent_config: { demo: true },
  },
  {
    id: "demo-sales",
    company_id: "demo-company",
    name: "Sales",
    slug: "sales",
    description: "Revenue AI for pipeline quality, account focus, and executive next actions.",
    department_type: "sales_ai",
    ai_agent_enabled: true,
    ai_agent_config: { demo: true },
  },
  {
    id: "demo-finance",
    company_id: "demo-company",
    name: "Finance",
    slug: "finance",
    description: "Finance AI for cash position, margin guardrails, and budget decisions.",
    department_type: "finance_ai",
    ai_agent_enabled: true,
    ai_agent_config: { demo: true },
  },
  {
    id: "demo-marketing",
    company_id: "demo-company",
    name: "Marketing",
    slug: "marketing",
    description: "Marketing AI for campaign focus, signal quality, and commercial proof points.",
    department_type: "marketing_ai",
    ai_agent_enabled: true,
    ai_agent_config: { demo: true },
  },
  {
    id: "demo-operations",
    company_id: "demo-company",
    name: "Operations",
    slug: "operations",
    description: "Operations AI for fulfillment capacity, service risk, and weekly execution.",
    department_type: "operations_ai",
    ai_agent_enabled: true,
    ai_agent_config: { demo: true },
  },
];

export const DEMO_KPIS = {
  ceo: [
    { title: "Revenue Run Rate", value: "$4.8M", detail: "+11.6% quarter over quarter" },
    { title: "Gross Margin", value: "31.4%", detail: "1.9 pts above guardrail" },
    { title: "Execution Risk", value: "Medium", detail: "Operations capacity is the constraint" },
  ],
  sales: [
    { title: "Qualified Pipeline", value: "$1.2M", detail: "68% tied to expansion accounts" },
    { title: "Win Rate", value: "27%", detail: "+4 pts after account segmentation" },
    { title: "Next Actions", value: "18", detail: "CEO-ready follow-ups due this week" },
  ],
  production: [
    { title: "Production Output", value: "18.4K", detail: "Cartons completed today" },
    { title: "Downtime", value: "45m", detail: "Packaging line issue" },
    { title: "Wastage", value: "2.1%", detail: "Above weekly guardrail" },
  ],
  finance: [
    { title: "Cash Coverage", value: "5.8 mo", detail: "Healthy with controlled hiring" },
    { title: "Discount Exposure", value: "$86K", detail: "Two deals require approval" },
    { title: "Budget Variance", value: "-3.2%", detail: "Below plan after vendor renegotiation" },
  ],
  marketing: [
    { title: "Qualified Demand", value: "412", detail: "High-intent accounts this month" },
    { title: "CAC Payback", value: "8.6 mo", detail: "Improved by 1.4 months" },
    { title: "Campaign Signal", value: "Strong", detail: "Operations proof points outperform" },
  ],
  operations: [
    { title: "OTIF", value: "91%", detail: "Distribution timing under watch" },
    { title: "Backlog", value: "23", detail: "Orders waiting dispatch" },
    { title: "Exceptions", value: "7", detail: "Route and stock issues" },
  ],
};

export const DEMO_REPORTS = {
  ceo: [
    { title: "Executive Operating Brief", detail: "Revenue growth remains healthy; fulfillment capacity is now the highest leverage decision." },
    { title: "Board Narrative", detail: "Jannat Al-Firdaws is moving from foundational setup to governed operational intelligence." },
  ],
  sales: [
    { title: "Pipeline Quality Review", detail: "Enterprise services and facilities accounts show the best margin-adjusted conversion." },
    { title: "Account Focus Plan", detail: "Prioritize 14 accounts with active budget, low delivery complexity, and renewal urgency." },
  ],
  production: [
    { title: "Production Control", detail: "Downtime and wastage are the highest leverage constraints for today's fulfillment plan." },
    { title: "Line Issue Review", detail: "Packaging reliability must be confirmed before Sales accepts delivery-heavy commitments." },
  ],
  finance: [
    { title: "Margin Guardrail Report", detail: "Finance should approve growth spend, but hold discounts above 8% for executive review." },
    { title: "Cash Discipline Memo", detail: "Working capital remains stable if procurement stays inside the approved replenishment model." },
  ],
  marketing: [
    { title: "Campaign Signal Review", detail: "Operational reliability messaging is outperforming generic productivity language." },
    { title: "Demand Generation Brief", detail: "Shift spend toward proof-led executive campaigns and reduce broad awareness placements." },
  ],
  operations: [
    { title: "Fulfillment Review", detail: "Route timing and warehouse staging are creating the current service-level risk." },
    { title: "Exception Queue", detail: "Escalate stock and delivery exceptions before they turn into customer commitments." },
  ],
};

export const DEMO_EXECUTIVE_SUMMARIES = {
  ceo: "Jannat Al-Firdaws is building toward governed operational intelligence at the poultry-field and enterprise level.",
  sales: "Sales should concentrate on expansion accounts with budget authority and low operational drag, then escalate only margin-sensitive deals.",
  production: "Production should protect output reliability first: resolve packaging downtime, reduce wastage, and confirm availability before Sales commits.",
  finance: "Finance can support the growth plan while preserving cash coverage, provided discounting and procurement commitments remain governed.",
  marketing: "Marketing should lead with operational reliability, measurable execution outcomes, and proof from high-fit commercial accounts.",
  operations: "Operations should focus on fulfillment reliability, exception clearance, and route discipline before accepting new service pressure.",
};

export const DEMO_FILES: CompanyFile[] = [
  demoFile("company_profile.md", null, 18400, "2026-05-12T09:15:00.000Z"),
  demoFile("executive_operating_brief_q2.md", null, 22600, "2026-05-13T11:30:00.000Z"),
  demoFile("board_demo_flow.md", null, 12600, "2026-05-13T14:40:00.000Z"),
  demoFile("sales_playbook.md", "demo-sales", 19800, "2026-05-14T10:20:00.000Z"),
  demoFile("finance_budget.md", "demo-finance", 15750, "2026-05-14T13:05:00.000Z"),
  demoFile("marketing_campaign.md", "demo-marketing", 17300, "2026-05-15T08:45:00.000Z"),
  demoFile("operations_sop.md", "demo-operations", 14220, "2026-05-15T12:10:00.000Z"),
];

export function getDemoWorkspaceKey(department: Department | null): keyof typeof DEMO_KPIS {
  if (!department) {
    return "ceo";
  }

  if (department.department_type === "sales_ai") {
    return "sales";
  }
  if (department.department_type === "production_ai") {
    return "production";
  }
  if (department.department_type === "finance_ai") {
    return "finance";
  }
  if (department.department_type === "marketing_ai") {
    return "marketing";
  }
  if (department.department_type === "operations_ai") {
    return "operations";
  }
  return "ceo";
}

export function getDemoChatTurns(department: Department | null) {
  const key = getDemoWorkspaceKey(department);
  return DEMO_CHAT_HISTORY[key];
}

const DEMO_CHAT_HISTORY = {
  ceo: [
    turn(
      "Give me the CEO briefing for this week.",
      "Revenue quality is improving, but execution risk is shifting from demand to fulfillment capacity.\n\nRecommended decision: approve the focused expansion plan for 14 high-fit accounts, keep discounts above 8% under Finance review, and ask Operations for a weekly capacity checkpoint before Sales commits to delivery-heavy proposals.",
      {
        priority: "Govern growth through capacity and margin",
        risks: ["Fulfillment pressure", "Discount leakage", "Unqualified expansion"],
        decision: "Approve focused account expansion with weekly operating review",
      },
    ),
  ],
  sales: [
    turn(
      "Which accounts should Sales prioritize this week?",
      "Prioritize expansion accounts with active budget, clear procurement ownership, and low delivery complexity.\n\nThe best near-term motion is a 14-account focus list: facilities management groups, multi-site offices, and hospitality operators with repeat purchasing patterns. Avoid low-margin one-off bids unless Finance approves the discount structure.",
      {
        segment: "Expansion accounts",
        next_actions: ["Confirm budget owner", "Attach replenishment bundle", "Escalate discounts above 8%"],
      },
    ),
  ],
  production: [
    turn(
      "What should Production fix today?",
      "Prioritize the packaging line issue before increasing output.\n\nThe 45 minutes of downtime and 2.1% wastage are already pressuring fulfillment and margin. Production should stabilize the line, confirm finished-goods availability with Warehouse, and give Sales a realistic commitment window before accepting delivery-heavy orders.",
      {
        bottleneck: "Packaging line downtime",
        next_actions: ["Stabilize line", "Confirm finished goods", "Update Sales commitment window"],
      },
    ),
  ],
  finance: [
    turn(
      "Give me the finance briefing for the growth plan.",
      "The growth plan is financially supportable if discounting remains controlled.\n\nCash coverage is healthy at 5.8 months. The main exposure is $86K in proposed discounts across two large opportunities. Finance should approve campaign spend, but require executive review for payment terms above 30 days or discounts above 8%.",
      {
        cash_coverage_months: 5.8,
        discount_exposure: "$86K",
        guardrail: "CEO approval for terms above 30 days",
      },
    ),
  ],
  marketing: [
    turn(
      "What message should Marketing emphasize now?",
      "Lead with operational reliability and measurable execution outcomes.\n\nCampaigns mentioning faster replenishment, fewer service interruptions, and accountable delivery operations are outperforming generic productivity language. Shift budget toward proof-led executive campaigns and use Sales feedback to refine account-specific messaging.",
      {
        message: "Operational reliability",
        channel_focus: ["Executive proof campaigns", "Account-based follow-up", "Sales enablement"],
      },
    ),
  ],
  operations: [
    turn(
      "Where is fulfillment risk coming from?",
      "Fulfillment risk is coming from handoff friction between production release, warehouse staging, and route timing.\n\nOperations should clear the exception queue, confirm stock availability before dispatch, and escalate repeated route failures to the CEO operating review.",
      {
        bottleneck: "Production-warehouse-distribution handoff",
        next_actions: ["Clear exceptions", "Confirm stock before dispatch", "Escalate route failures"],
      },
    ),
  ],
};

function turn(userMessage: string, ceoText: string, logic: Record<string, unknown>) {
  return {
    id: `demo-${userMessage.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
    userMessage,
    response: demoResponse(ceoText, logic),
  };
}

function demoResponse(ceoText: string, logic: Record<string, unknown>): ChatResponse {
  return {
    ceo_text: ceoText,
    logic_json: {
      demo_mode: true,
      confidence: "high",
      ...logic,
    },
    followup_question: null,
    meta: {
      company_id: "demo-company",
      session_id: "investor-demo",
      context: {
        dataset: "Jannat Al-Firdaws operational demo",
      },
      parse_ok: true,
      memory_injected: true,
      events_count: 12,
    },
  };
}

function demoFile(filename: string, departmentId: string | null, size: number, createdAt: string): CompanyFile {
  return {
    id: `demo-file-${filename}`,
    company_id: "demo-company",
    department_id: departmentId,
    uploaded_by_user_id: "demo-user",
    filename,
    content_type: "text/markdown",
    file_size_bytes: size,
    status: "ready",
    metadata: { demo: true },
    created_at: createdAt,
    updated_at: createdAt,
  };
}
