"""DEPLOY-F1 regression: the deploy-time migration command must be invoked
as a module (`python -m scripts.migrate`), never as a bare script path
(`python scripts/migrate.py`) - the bare form fails with
`ModuleNotFoundError: No module named 'app'` because `scripts/migrate.py`
imports `app.core.config`, which only resolves when the repository root is
on `sys.path` (as it is under `-m`, but not for a bare script invocation).
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CORRECT_COMMAND = "python -m scripts.migrate"
OBSOLETE_COMMAND = "python scripts/migrate.py"

DEPLOYMENT_DOCS = [
    REPO_ROOT / "docs" / "deployment" / "render_backend.md",
    REPO_ROOT / "docs" / "deployment" / "neon_database.md",
    REPO_ROOT / "docs" / "deployment" / "first_deploy_checklist.md",
]


def test_render_yaml_pre_deploy_uses_module_invocation() -> None:
    content = (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")
    assert f"preDeployCommand: {CORRECT_COMMAND}" in content


def test_render_yaml_does_not_use_obsolete_bare_script_invocation() -> None:
    content = (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")
    assert OBSOLETE_COMMAND not in content


def test_deployment_docs_do_not_instruct_obsolete_bare_script_invocation() -> None:
    for doc_path in DEPLOYMENT_DOCS:
        content = doc_path.read_text(encoding="utf-8")
        assert OBSOLETE_COMMAND not in content, f"{doc_path} still instructs the obsolete invocation form"


def test_deployment_docs_reference_the_correct_module_invocation() -> None:
    for doc_path in DEPLOYMENT_DOCS:
        content = doc_path.read_text(encoding="utf-8")
        assert CORRECT_COMMAND in content, f"{doc_path} does not reference the correct invocation form"
