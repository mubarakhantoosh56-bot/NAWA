# Agent Instructions

Before making any change, read:

1. `docs/nawa_brain/README.md`
2. `docs/nawa_brain/09_agent_instructions.md`

For product, UI, backend, data, or architecture work, also read the relevant NAWA Brain files in this folder.

## Naming

Use **NAWA** as the current product name.

Treat **AIMX** as historical legacy only. Do not introduce new AIMX branding, UI language, architecture direction, or documentation unless explicitly documenting legacy context.

## Product Direction

NAWA is the Company Brain.

Do not turn NAWA into:

- ERP-first UI
- A plain chatbot
- A static dashboard
- A pile of isolated modules

Every feature should strengthen the Company Brain:

- Understand organization
- Capture inputs
- Preserve memory
- Analyze operational context
- Connect departments and workflows
- Support reports, SOPs, PPT, avatar/video, voice, and automations

## Engineering Rules

Preserve:

- Auth
- Multi-tenant isolation
- Role visibility
- Bilingual support
- Operational memory
- Decision context
- Pattern detection
- Existing routes unless change is necessary

Prefer lightweight MVP structures that can later connect to ERP, HR, accounting, attendance, sales, and warehouse systems.

If runtime code changes are not required, keep the work docs-only.

