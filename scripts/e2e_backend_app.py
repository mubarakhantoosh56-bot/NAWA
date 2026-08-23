"""M7 Slice 3C: E2E-only backend bootstrap for the Golden A browser E2E run.

Not a production entrypoint - app/main.py is untouched and remains the only
thing Render/normal deployment ever runs (see render.yaml). This module
exists purely as a Uvicorn *target* scripts/e2e_orchestrator.py points at
instead of app.main:app, only for its own isolated E2E backend process.

It imports the real, unmodified FastAPI application and swaps exactly one
seam before serving it: `ai_engine.client`, the same attribute the backend
Golden Journey test replaces (tests/test_m7_slice1_upload_truth_bridge.py,
`ai_engine.client = fake_client`). Every route, service, repository,
dependency, and piece of reasoning/evidence logic in `app` is the real,
unmodified production object graph - only the outbound LLM completion call
is deterministic instead of live OpenAI.

Required environment (set by scripts/e2e_orchestrator.py):
    E2E_GOLDEN_HALL_NUMBER - the deterministic hall number the fake client
        looks for (as entity_reference) in the real reasoning reference
        catalog (see scripts/e2e_fake_ai_client.py and
        scripts/e2e_golden_fixture.py).
    DECISION_CONTEXT_DEBUG=true - required for the fake to read the real
        decision context snapshot (app.services.decision_debug).

Usage (only ever invoked by scripts/e2e_orchestrator.py):
    uvicorn scripts.e2e_backend_app:app --host 127.0.0.1 --port <port>
"""
from __future__ import annotations

import os

from app.main import app
from app.services.openai_client import ai_engine
from scripts.e2e_fake_ai_client import E2EGoldenFakeOpenAIClient

_hall_number = os.environ.get("E2E_GOLDEN_HALL_NUMBER", "")
if not _hall_number:
    raise RuntimeError(
        "E2E_GOLDEN_HALL_NUMBER is required to start scripts.e2e_backend_app - "
        "this entrypoint is E2E-only and must never be used for production serving"
    )

ai_engine.client = E2EGoldenFakeOpenAIClient(hall_number=_hall_number)

__all__ = ["app"]
