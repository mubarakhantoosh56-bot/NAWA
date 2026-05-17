# NAWA Mock Company Trial Plan

Use this plan to test the current NAWA MVP manually before connecting n8n or onboarding a real pilot company. The goal is to learn how the product behaves with believable company context, where the UX feels thin, which fields are missing, and whether AI responses are useful enough for an executive workflow.

This is a no-integration trial. Do not add n8n workflows yet.

## 1. Trial Company Profile

Company name: Northstar Commercial Group

Industry: B2B commercial services and supply operations

Company size: 186 employees

Operating model:

- Serves multi-site offices, facilities teams, hospitality operators, and service-led businesses.
- Sells repeat replenishment bundles, managed service support, and account-based commercial contracts.
- Operates with Sales, Finance, Marketing, Operations, and CEO-level executive oversight.
- Current quarter focus is moving from opportunistic growth to governed execution.

Current business objective:

Increase qualified enterprise expansion revenue by 18 percent this quarter while protecting margin, cash coverage, and fulfillment reliability.

Core constraints:

- Fulfillment capacity is the main constraint on new commitments.
- Discounts above 8 percent require Finance review.
- Payment terms longer than 30 days require CEO approval.
- Gross margin guardrail is 30 percent.
- Cash coverage is 5.8 months.

Executive narrative:

NAWA should feel like an institutional decision layer. It should connect company knowledge, department context, risks, and recommended next actions without feeling like a generic chatbot.

## 2. Departments

CEO AI:
Company-wide executive assistant for priorities, risks, cross-functional decisions, and investor-ready summaries.

Sales AI:
Revenue assistant for pipeline quality, account focus, discount escalation, and next-best action.

Finance AI:
Financial control assistant for cash coverage, margin guardrails, budget variance, payment terms, and risk review.

Marketing AI:
Campaign intelligence assistant for positioning, proof points, demand signals, and channel focus.

Operations AI:
Execution assistant for capacity, fulfillment risk, delivery commitments, and service reliability.

## 3. Demo Files

Use these files as the mock company knowledge base.

| Filename | Scope | Description |
| --- | --- | --- |
| `company_profile.md` | Company-wide | Overview of Northstar, operating model, objectives, constraints, and executive priority. |
| `growth_goals.md` | Company-wide | Quarterly growth goals, margin rules, account focus, and decision ownership expectations. |
| `executive_operating_brief_q2.md` | CEO AI | CEO summary of revenue quality, execution risk, margin control, and recommended decisions. |
| `board_demo_flow.md` | CEO AI | Investor demo narrative and walkthrough order for CEO, Sales, Finance, Marketing, and Operations. |
| `sales_playbook.md` | Sales AI | Expansion account criteria, weekly actions, discount escalation, and sales reporting expectations. |
| `finance_budget.md` | Finance AI | Cash coverage, gross margin guardrail, discount exposure, payment terms, and finance recommendations. |
| `marketing_campaign.md` | Marketing AI | Proof-led campaign strategy, operating reliability messaging, channels, and campaign KPIs. |
| `operations_sop.md` | Operations AI | Fulfillment capacity, delivery-risk rules, procurement commitments, and service-risk metrics. |

## 4. Demo KPIs

CEO AI:

- Revenue run rate: `$4.8M`
- Gross margin: `31.4%`
- Execution risk: `Medium`
- Strategic decision: approve focused expansion only with capacity checkpoints

Sales AI:

- Qualified pipeline: `$1.2M`
- Win rate: `27%`
- Account focus list: `14 accounts`
- Discount escalations: `2 opportunities`

Finance AI:

- Cash coverage: `5.8 months`
- Gross margin guardrail: `30%`
- Discount exposure: `$86K`
- Budget variance: `-3.2%`

Marketing AI:

- Qualified demand signals: `412`
- CAC payback: `8.6 months`
- Campaign signal: operational reliability is strongest
- Weekly proof assets: `2`

Operations AI:

- Capacity utilization: `82%`
- Late delivery risk: `Medium`
- Delivery-heavy proposals needing review: `5`
- Service-risk accounts: `3`

## 5. Test Prompts And Expected AI Behavior

### CEO AI

Prompt:
Give me the CEO briefing for this week: risks, priorities, and recommended actions.

Expected behavior:

- Summarizes revenue quality, fulfillment capacity, margin control, and account focus.
- Names specific risks instead of generic warnings.
- Recommends a clear executive decision.
- Mentions Sales, Finance, and Operations ownership.

Prompt:
What should Northstar focus on before a NAWA investor demo?

Expected behavior:

- Produces a crisp investor-demo narrative.
- Highlights the product value: knowledge to operational intelligence.
- Suggests showing CEO, Sales, Finance, and Marketing flows.
- Avoids overclaiming automation or integrations that do not exist yet.

Prompt:
Summarize the top cross-department decisions we should make today.

Expected behavior:

- Groups decisions by owner.
- Identifies dependencies between Sales, Finance, Marketing, and Operations.
- Uses the margin and capacity constraints.

### Sales AI

Prompt:
Summarize the sales pipeline and highlight the best next actions.

Expected behavior:

- Prioritizes the 14-account focus list.
- Mentions budget owner, delivery complexity, and expansion fit.
- Escalates discount-sensitive deals to Finance.

Prompt:
Which expansion accounts should Sales prioritize this month?

Expected behavior:

- Prioritizes accounts with active budget and low operational drag.
- Avoids broad sales advice.
- Connects recommended accounts to Operations capacity.

Prompt:
What should Sales report to the CEO before the demo?

Expected behavior:

- Reports pipeline quality, next actions, discount exposure, and operational dependencies.
- Uses concise executive language.

### Finance AI

Prompt:
Give me a finance briefing with cash, margin, and spending risks.

Expected behavior:

- Mentions 5.8 months cash coverage.
- Mentions 30 percent gross margin guardrail.
- Flags $86K discount exposure.
- Separates acceptable growth spend from risky pricing exceptions.

Prompt:
Which costs should Finance review before the next planning meeting?

Expected behavior:

- Reviews discounts, payment terms, campaign spend, procurement commitments, and delivery-heavy commitments.
- Recommends approval rules.

Prompt:
What finance questions should the CEO ask today?

Expected behavior:

- Produces focused questions, not a long finance essay.
- Helps the CEO decide what needs approval, delay, or review.

### Marketing AI

Prompt:
Summarize current marketing priorities and campaign opportunities.

Expected behavior:

- Emphasizes operational reliability and measurable outcomes.
- Avoids generic awareness campaign language.
- Connects campaigns to Sales focus accounts.

Prompt:
Which messages should Marketing emphasize for growth this month?

Expected behavior:

- Recommends proof-led messaging.
- Mentions reliability, fewer service interruptions, and accountable delivery.
- Suggests campaign assets that Sales can use.

Prompt:
What marketing proof points should we show in an investor demo?

Expected behavior:

- Explains why proof-led campaigns matter.
- Names metrics: qualified demand, CAC payback, campaign signal quality.

### Operations AI

Prompt:
What fulfillment risks could block the expansion plan?

Expected behavior:

- Identifies capacity utilization, delivery-heavy proposals, procurement exceptions, and service-risk accounts.
- Recommends a weekly capacity checkpoint.

Prompt:
Which commitments should Operations review before Sales sends proposals?

Expected behavior:

- Lists custom delivery terms, large replenishment commitments, unusual payment terms, and capacity-heavy accounts.
- Connects Operations review to margin and service reliability.

Prompt:
Create a weekly operating checklist for the expansion plan.

Expected behavior:

- Produces a concise checklist with owners and metrics.
- Avoids generic project-management filler.

## 6. Manual QA Checklist

Login and workspace:

- Can log in with the mock company credentials.
- Company name displays correctly.
- CEO AI is available as the default workspace.
- Sales, Finance, Marketing, and Operations are visible.
- Department switching is clear and does not reset the whole page unexpectedly.

Dashboard and demo data:

- KPI cards feel believable and department-specific.
- Executive summary changes when switching departments.
- Reports feel like real operating artifacts.
- Files list shows meaningful filenames and scopes.
- Empty states do not appear during the intended demo path.

Chat UX:

- Suggested prompts are useful and specific.
- Prompt cards fill the composer for review before sending.
- Chat history feels realistic.
- AI response formatting is readable.
- Decision logic panel is useful but not visually dominant.
- Loading state feels calm and credible.

AI usefulness:

- Responses cite or reflect company constraints.
- Responses avoid generic SaaS phrasing.
- Responses include owners, risks, metrics, and next actions.
- Department AI stays in its lane.
- CEO AI can synthesize across departments.
- AI does not invent n8n workflows or claim integrations are live.

Security and tenant behavior:

- No tokens, passwords, or `.env` values appear in the UI.
- Company data appears tenant-scoped.
- Locked/permission states are understandable if using restricted roles.

Responsive behavior:

- Workspace is usable on laptop widths.
- Panels do not overlap.
- Chat composer remains usable.
- Files panel does not crowd the main chat surface.

## 7. Bug And UX Notes Template

Use this format for every issue found.

```markdown
## Issue

Title:

Area:
CEO AI / Sales AI / Finance AI / Marketing AI / Operations AI / Files / Navigation / Auth / Layout / Other

Severity:
Blocker / High / Medium / Low

Steps to reproduce:
1.
2.
3.

Expected:

Actual:

Why it matters for pilot:

Suggested fix:

Screenshot or notes:
```

## 8. Readiness Checklist Before Real Pilot

Product flow:

- Mock company demo can be completed end to end without explaining missing context.
- CEO, Sales, Finance, Marketing, and Operations each feel distinct.
- AI answers are useful enough to support a real business conversation.
- Demo files are visible and understandable.
- The product communicates where data comes from and what AI is doing.

Data model:

- Required company fields are known.
- Required department fields are known.
- Required file metadata is known.
- Required KPI fields are known.
- Required prompt and response fields are known.

UX:

- First-time login and workspace entry are clear.
- Empty states are useful.
- Loading states feel polished.
- Error messages are actionable.
- The UI feels calm, executive, and not demo-fragile.

AI behavior:

- Responses stay grounded in uploaded knowledge.
- Responses identify risks and owners.
- Responses produce decisions, not only summaries.
- Responses do not expose internal prompts or irrelevant implementation details.
- Department scope works as expected.

Operations:

- Demo reset process is documented.
- Test credentials are local and safe.
- No real company data is used.
- No n8n dependency is required.
- Known bugs are triaged before real pilot.

Pilot gate:

- At least one full mock-company walkthrough completed.
- All blocker and high-severity issues resolved.
- Medium issues have an owner or workaround.
- Real pilot onboarding fields are documented.
- n8n integration requirements are based on observed product gaps, not assumptions.
