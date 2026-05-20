# Data Capture Architecture

NAWA follows a no-input-lost principle.

Every input should be stored first as raw input, then parsed and classified into operational intelligence.

## Pipeline

```text
Input
→ Raw Input Storage
→ Parsing / Entity Extraction
→ Classification
→ Structured Record Draft
→ Operational Event
→ Pattern Detection
→ Decision Context
→ AI Insight
```

## Source Types

Supported or planned source types:

- Chat
- Forms
- Files
- Images
- Integrations
- Automations
- ERP systems
- HR systems
- Accounting systems
- Attendance systems
- Sales systems
- Warehouse systems

## Native Operational Mode

If a company has no ERP, NAWA must still work.

Native Operational Mode uses:

- Chat/manual notes
- Universal update panel
- File uploads
- Lightweight forms
- Future automations

This allows NAWA to become useful before full system integration.

