"""M7 Slice 3B: browser E2E orchestration entrypoint.

Owns: E2E database validation, the frontend production build, and the
full lifecycle (start/readiness/VERIFIED stop) of BOTH long-running
application processes - backend and frontend. Playwright owns nothing but
the browser test run itself (see frontend/playwright.config.ts: no
`webServer`).

M7 Slice 3B Correction Round 4: a Windows diagnostic under the actual
restricted reviewer token (a Medium-integrity, non-elevated account) proved
that `taskkill /PID <pid> /T /F` - the termination primitive used through
Round 3 - fails there with "Access denied", even though the exact same PID
terminates successfully via `Popen.kill()` using the process handle this
orchestrator already holds from spawning the child. `taskkill.exe` must
re-open the target PID from scratch (`OpenProcess` + `PROCESS_TERMINATE`),
which the restricted token cannot do for a process it didn't create;
`Popen.kill()` needs no such re-open because Windows already granted full
rights on that handle at `CreateProcess` time. Root termination on Windows
is therefore now done exclusively via the retained handle - no executable
is spawned merely to kill something. Since this guarantees only the owned
root's own termination (not an arbitrary descendant tree the way a
recursive tree-kill claims to), backend/frontend cleanup additionally
verifies their known service port is actually released, which is the
concrete, previously-observed failure mode (a live listener despite an
apparently-dead root) this is meant to catch.

Usage (from repo root or frontend/, both work):
    python scripts/e2e_orchestrator.py

Required environment:
    E2E_DATABASE_URL - an isolated PostgreSQL URL whose database name
        contains "e2e" and differs from the ambient DATABASE_URL. See
        scripts/e2e_db_guard.py for the exact safety contract. There is no
        fallback: a missing or unsafe value stops this script before any
        build, migration, or process is started.

Optional environment:
    E2E_BACKEND_PORT (default: 8100)
    E2E_FRONTEND_PORT (default: 3100)
"""
from __future__ import annotations

import contextlib
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_BACKEND_PORT = "8100"
DEFAULT_FRONTEND_PORT = "3100"
BACKEND_HEALTH_TIMEOUT_SECONDS = 60
FRONTEND_READY_TIMEOUT_SECONDS = 60
HTTP_POLL_INTERVAL_SECONDS = 1.0
FRONTEND_BUILD_TIMEOUT_SECONDS = 300
PLAYWRIGHT_TIMEOUT_SECONDS = 600
STOP_WAIT_TIMEOUT_SECONDS = 10.0
PORT_RELEASE_TIMEOUT_SECONDS = 8.0
PORT_POLL_INTERVAL_SECONDS = 0.5
LOG_TAIL_MAX_BYTES = 2000
IS_WINDOWS = sys.platform.startswith("win")


class OrchestrationError(RuntimeError):
    """Raised when the E2E environment cannot be safely established."""


# ---------------------------------------------------------------------------
# Owned-process primitive: one strategy, reused for the frontend build,
# backend, frontend server, and Playwright run. A process is only ever
# force-killed while confirmed still alive; an already-exited root's PID is
# never targeted, since a numeric PID can be reused by the OS for an
# unrelated process once its original owner has exited. Termination is only
# ever reported successful once actually verified - never merely attempted.
# Root termination uses the process handle this orchestrator already holds
# (`Popen.kill()`) rather than spawning a separate kill executable - see the
# module docstring for why that matters under a restricted Windows token.
# ---------------------------------------------------------------------------


@dataclass
class OwnedProcess:
    name: str
    process: subprocess.Popen[bytes]
    log_file: object | None = None  # open file handle when stdio is isolated; else None
    service_port: int | None = None  # if set, cleanup also verifies this port is released


@dataclass(frozen=True)
class StopResult:
    name: str
    was_alive: bool
    success: bool
    message: str


def is_port_listening(host: str, port: int, connect_timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=connect_timeout):
            return True
    except OSError:
        return False


def wait_for_port_release(host: str, port: int, timeout_seconds: float) -> bool:
    """Bounded, localhost-only check that nothing is listening on `port` anymore.

    Never kills anything - purely observational. This is the second half of
    the cleanup contract for backend/frontend: verifying the *root process*
    exited does not, by itself, prove no descendant inherited its listening
    socket, so the port itself is checked directly.
    """
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not is_port_listening(host, port):
            return True
        time.sleep(PORT_POLL_INTERVAL_SECONDS)
    return not is_port_listening(host, port)


def spawn_owned_process(
    name: str,
    args: list[str],
    cwd: Path,
    env: dict[str, str],
    isolate_stdio: bool = False,
    service_port: int | None = None,
) -> OwnedProcess:
    """Spawn a process this orchestrator owns the full lifecycle of.

    `isolate_stdio=True` (used for the long-lived backend/frontend servers)
    redirects the child's stdout/stderr to a dedicated temp file instead of
    inheriting the caller's handles - a long-running service must never
    hold a write handle to whatever pipe a reviewing/CI parent is reading
    this command's own output through, since that would block that parent
    from ever seeing EOF even after this orchestrator itself has exited.
    Build and Playwright output remain inherited (isolate_stdio=False, the
    default) since their output should stay user-visible.

    `service_port`, when set, is checked for release during cleanup (see
    `stop_owned_process`) - use it for the backend/frontend servers, not for
    the build or Playwright, which own no listening port themselves.
    """
    popen_kwargs: dict[str, object] = {}
    if IS_WINDOWS:
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    log_file = None
    if isolate_stdio:
        log_file = tempfile.NamedTemporaryFile(prefix=f"nawa_e2e_{name}_", suffix=".log", delete=False)
        popen_kwargs["stdout"] = log_file
        popen_kwargs["stderr"] = subprocess.STDOUT

    process = subprocess.Popen(args, cwd=cwd, env=env, **popen_kwargs)
    return OwnedProcess(name=name, process=process, log_file=log_file, service_port=service_port)


def _kill_root_once(process: subprocess.Popen[bytes]) -> None:
    """Terminate the owned root using the process handle this orchestrator
    already holds - not by spawning taskkill/another executable.

    On Windows, `Popen.kill()` calls `TerminateProcess` on the handle
    returned when this orchestrator itself created the child; that handle
    already carries full rights, unlike a fresh `OpenProcess` call (what
    `taskkill.exe` must do), which a restricted reviewer token was proven
    to deny. This guarantees termination of the root only - not an
    arbitrary descendant tree - so backend/frontend cleanup separately
    verifies their service port is released (see `wait_for_port_release`).
    """
    if IS_WINDOWS:
        process.kill()
    else:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)


def _wait_confirmed_exited(process: subprocess.Popen[bytes], timeout: float) -> bool:
    """True only once the root's exit is actually confirmed, never assumed."""
    try:
        process.wait(timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        # `wait` can time out a hair before the process actually exits; a
        # direct poll() catches that race without waiting the full budget
        # again. If this is still None, the root really is still alive.
        return process.poll() is not None


def stop_owned_process(owned: OwnedProcess, timeout: float = STOP_WAIT_TIMEOUT_SECONDS) -> StopResult:
    """Stop an owned process - only if its root is confirmed alive - and only
    ever report success once termination (and, for a service, port release)
    is actually verified.

    If the root already exited on its own, no kill is attempted: re-killing
    a PID that no longer belongs to our process risks hitting an unrelated
    process the OS may have since reused that PID for. Otherwise this makes
    up to two scoped kill+verify attempts (never an unbounded retry loop)
    and reports failure - not success - if the root is still alive after
    both. This proves only that the owned ROOT exited, not an entire
    process tree; when `service_port` is set, the port is independently
    checked to catch a surviving descendant that inherited the listener.
    """
    process = owned.process
    try:
        already_dead = process.poll() is not None
        if already_dead:
            exited = True
        else:
            _kill_root_once(process)
            exited = _wait_confirmed_exited(process, timeout)
            if not exited:
                _kill_root_once(process)
                exited = _wait_confirmed_exited(process, timeout)

        if not exited:
            return StopResult(
                name=owned.name,
                was_alive=True,
                success=False,
                message=(
                    f"{owned.name} (pid={process.pid}) FAILED to verify root termination after 2 kill "
                    "attempts; it may still be alive"
                ),
            )

        root_note = (
            f"{owned.name} (pid={process.pid}) had already exited on its own (code={process.returncode})"
            if already_dead
            else f"{owned.name} (pid={process.pid}) root process was verified terminated"
        )

        if owned.service_port is None:
            return StopResult(name=owned.name, was_alive=not already_dead, success=True, message=root_note)

        if wait_for_port_release("127.0.0.1", owned.service_port, PORT_RELEASE_TIMEOUT_SECONDS):
            return StopResult(
                name=owned.name,
                was_alive=not already_dead,
                success=True,
                message=f"{root_note} and port {owned.service_port} is released",
            )
        return StopResult(
            name=owned.name,
            was_alive=not already_dead,
            success=False,
            message=(
                f"{root_note}, but port {owned.service_port} is still listening after "
                f"{PORT_RELEASE_TIMEOUT_SECONDS}s (unexpected surviving descendant?)"
            ),
        )
    finally:
        if owned.log_file is not None:
            with contextlib.suppress(OSError):
                owned.log_file.close()
            with contextlib.suppress(OSError):
                os.unlink(owned.log_file.name)


@dataclass(frozen=True)
class PlaywrightOutcome:
    """Pure result of a completed (or forcibly ended) Playwright run."""

    exit_code: int
    timed_out: bool
    message: str


def resolve_playwright_outcome(returncode: int | None, timed_out: bool) -> PlaywrightOutcome:
    """Decide the final orchestrator exit code/message for a Playwright run.

    Pure and side-effect-free so it is unit-testable without launching any
    real process. A timeout always yields a non-zero exit code - it is
    never used to synthesize a successful result.
    """
    if timed_out:
        return PlaywrightOutcome(
            exit_code=1,
            timed_out=True,
            message=(
                f"Playwright run exceeded {PLAYWRIGHT_TIMEOUT_SECONDS}s and was force-terminated "
                "(this is a defensive bound, not a normal outcome)"
            ),
        )
    if returncode is None:
        raise ValueError("returncode must be set when timed_out is False")
    if returncode == 0:
        return PlaywrightOutcome(exit_code=0, timed_out=False, message="Playwright run completed normally")
    return PlaywrightOutcome(
        exit_code=returncode, timed_out=False, message=f"Playwright run failed with exit code {returncode}"
    )


def resolve_final_exit_code(playwright_exit_code: int, cleanup_failed: bool) -> int:
    """Combine the browser-test result with cleanup verification into one exit code.

    Pure and side-effect-free. A verified-failed cleanup always makes the
    overall command non-zero, even if the browser tests passed - but never
    masks an already-failing browser result behind a generic code.
    """
    if cleanup_failed:
        return 1 if playwright_exit_code == 0 else playwright_exit_code
    return playwright_exit_code


# ---------------------------------------------------------------------------
# Direct CLI command construction - node + a repository-resolved CLI script,
# never npm/npx, so the canonical path never spawns an extra shell/npm.cmd
# layer for any long-lived or bounded-build process this orchestrator owns.
# ---------------------------------------------------------------------------


def _resolve_next_cli() -> Path:
    return FRONTEND_DIR / "node_modules" / "next" / "dist" / "bin" / "next"


def _resolve_playwright_cli() -> Path:
    return FRONTEND_DIR / "node_modules" / "@playwright" / "test" / "cli.js"


def build_frontend_build_command() -> list[str]:
    node_path = _require_executable("node")
    return [node_path, str(_resolve_next_cli()), "build"]


def build_frontend_start_command(port: str, hostname: str = "127.0.0.1") -> list[str]:
    node_path = _require_executable("node")
    return [node_path, str(_resolve_next_cli()), "start", "-p", port, "-H", hostname]


def build_playwright_command() -> list[str]:
    node_path = _require_executable("node")
    return [node_path, str(_resolve_playwright_cli()), "test"]


def _ambient_database_url() -> str:
    """Best-effort resolution of the operator's normal DATABASE_URL.

    Mirrors what `app.core.config` would resolve without mutating this
    process's environment, so the safety guard can compare against it.
    """
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    dotenv_path = REPO_ROOT / ".env"
    if dotenv_path.exists():
        return dotenv_values(dotenv_path).get("DATABASE_URL") or ""
    return ""


def _require_executable(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise OrchestrationError(f"Required executable {name!r} was not found on PATH")
    return resolved


def _read_log_tail(owned: OwnedProcess, max_bytes: int = LOG_TAIL_MAX_BYTES) -> str:
    if owned.log_file is None:
        return ""
    try:
        data = Path(owned.log_file.name).read_bytes()
    except OSError:
        return ""
    return data[-max_bytes:].decode("utf-8", errors="replace")


def _wait_for_http_ready(service_name: str, url: str, owned: OwnedProcess, timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        if owned.process.poll() is not None:
            tail = _read_log_tail(owned)
            suffix = f"\n--- last {service_name} output ---\n{tail}" if tail else ""
            raise OrchestrationError(
                f"E2E {service_name} process exited early (exit code {owned.process.returncode}) "
                f"before becoming ready{suffix}"
            )
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError, TimeoutError) as error:
            last_error = error
        time.sleep(HTTP_POLL_INTERVAL_SECONDS)

    tail = _read_log_tail(owned)
    suffix = f"\n--- last {service_name} output ---\n{tail}" if tail else ""
    raise OrchestrationError(
        f"E2E {service_name} never became ready at {url} within {timeout_seconds}s: {last_error}{suffix}"
    )


def run_frontend_build(env: dict[str, str]) -> None:
    """Run the production frontend build as a bounded step, owned like any other.

    Deliberately not part of Playwright's config (Playwright owns no
    servers at all now) and deliberately bounded: an unbounded build could
    hang the whole canonical command exactly like the original defect, just
    earlier in the pipeline. Output stays inherited/visible (not isolated).
    """
    command = build_frontend_build_command()
    owned = spawn_owned_process("frontend-build", command, cwd=FRONTEND_DIR, env=env)

    try:
        returncode = owned.process.wait(timeout=FRONTEND_BUILD_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        stop_result = stop_owned_process(owned)
        raise OrchestrationError(
            f"Frontend production build exceeded {FRONTEND_BUILD_TIMEOUT_SECONDS}s and was terminated "
            f"({stop_result.message})"
        ) from None

    if returncode != 0:
        raise OrchestrationError(f"Frontend production build failed (exit code {returncode})")


def run_migrations(env: dict[str, str]) -> None:
    # Invoked as `-m scripts.migrate` (not as a bare script path) so that
    # `app.core.config` resolves correctly regardless of the caller's cwd.
    result = subprocess.run(
        [sys.executable, "-m", "scripts.migrate"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise OrchestrationError(
            f"E2E migrations failed against the isolated database (exit code {result.returncode})"
        )


def start_backend(port: str, env: dict[str, str]) -> OwnedProcess:
    # M7 Slice 3C: served through scripts.e2e_backend_app, not app.main,
    # so the deterministic Golden A fake AI client can be injected at the
    # ai_engine.client seam before Uvicorn starts accepting connections -
    # see that module's docstring. app/main.py itself is never modified.
    return spawn_owned_process(
        "backend",
        [
            sys.executable, "-m", "uvicorn", "scripts.e2e_backend_app:app",
            "--host", "127.0.0.1", "--port", port,
        ],
        cwd=REPO_ROOT,
        env=env,
        isolate_stdio=True,
        service_port=int(port),
    )


def run_seed_jannat(env: dict[str, str]) -> None:
    """Seed the Jannat Al-Firdaws company/owner/departments into the E2E
    database, using the existing idempotent scripts/seed_jannat.py.

    `env` is the already-guard-verified backend_env (DATABASE_URL bound to
    E2E_DATABASE_URL by e2e_db_guard.py in main(), never the ambient/local
    DATABASE_URL) - seed_jannat.py reads DATABASE_URL and DEMO_OWNER_PASSWORD
    from exactly this environment, so this can never reach a non-E2E
    database.
    """
    result = subprocess.run(
        [sys.executable, "-m", "scripts.seed_jannat"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise OrchestrationError(
            f"E2E Jannat seeding failed against the isolated database (exit code {result.returncode})"
        )


def resolve_jannat_company_id(database_url: str) -> str:
    """Look up the just-seeded Jannat Al-Firdaws company's real id.

    Required because app.services.operational_truth_context.is_jannat_tenant
    fail-closed-gates the uploaded-file -> Operational Truth Context bridge
    behind settings.JANNAT_COMPANY_ID matching the authenticated company's
    id exactly - and seed_jannat.py's company id is only known after it
    runs (gen_random_uuid(), fresh per database). The backend Golden Journey
    test achieves the same effect in-process via monkeypatch
    (_configure_jannat_company_id); this is the equivalent for a real,
    separately-started backend subprocess - JANNAT_COMPANY_ID is injected
    into backend_env before Uvicorn starts, exactly once, read-only lookup.
    """
    import asyncio

    import asyncpg

    from scripts.seed_jannat import COMPANY_SLUG

    async def _lookup() -> str:
        conn = await asyncpg.connect(dsn=database_url, timeout=15)
        try:
            row = await conn.fetchrow("SELECT id FROM companies WHERE slug = $1", COMPANY_SLUG)
        finally:
            await conn.close()
        if row is None:
            raise OrchestrationError(
                f"Jannat Al-Firdaws (slug={COMPANY_SLUG!r}) not found in the E2E database after seeding"
            )
        return str(row["id"])

    return asyncio.run(_lookup())


def wait_for_backend_health(port: str, owned: OwnedProcess) -> None:
    _wait_for_http_ready("backend", f"http://127.0.0.1:{port}/health", owned, BACKEND_HEALTH_TIMEOUT_SECONDS)


def start_frontend(port: str, env: dict[str, str]) -> OwnedProcess:
    command = build_frontend_start_command(port)
    return spawn_owned_process(
        "frontend", command, cwd=FRONTEND_DIR, env=env, isolate_stdio=True, service_port=int(port)
    )


def wait_for_frontend_ready(port: str, owned: OwnedProcess) -> None:
    _wait_for_http_ready("frontend", f"http://127.0.0.1:{port}/login", owned, FRONTEND_READY_TIMEOUT_SECONDS)


def run_playwright(env: dict[str, str]) -> int:
    command = build_playwright_command()
    owned = spawn_owned_process("playwright", command, cwd=FRONTEND_DIR, env=env)

    timed_out = False
    returncode: int | None = None
    try:
        returncode = owned.process.wait(timeout=PLAYWRIGHT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        timed_out = True

    # No-op if Playwright already exited on its own (the normal case); only
    # actually terminates the root if the bounded wait above timed out.
    stop_result = stop_owned_process(owned)

    outcome = resolve_playwright_outcome(returncode, timed_out)
    print(f"[e2e] {outcome.message}")
    print(f"[e2e] {stop_result.message}")
    return outcome.exit_code


def main() -> int:
    from scripts.e2e_db_guard import UnsafeE2EDatabaseError, assert_safe_e2e_database_url
    from scripts.e2e_golden_fixture import (
        GOLDEN_FIXTURE_FILENAME,
        GOLDEN_HALL_NUMBER,
        GOLDEN_MARKER,
        write_golden_workbook,
    )

    e2e_database_url = os.environ.get("E2E_DATABASE_URL", "")
    ambient_url = _ambient_database_url()

    try:
        assert_safe_e2e_database_url(e2e_database_url, ambient_default_url=ambient_url)
    except UnsafeE2EDatabaseError as error:
        print(f"[e2e] REFUSING TO PROCEED: {error}", file=sys.stderr)
        return 1

    # Fail closed before any migration/seed/backend/Playwright step - no
    # fallback password literal exists anywhere in this file. The real
    # seeded Jannat owner's password must come only from the operator's
    # environment (never printed here or anywhere else in this module).
    demo_owner_password = os.environ.get("DEMO_OWNER_PASSWORD", "").strip()
    if not demo_owner_password:
        print("[e2e] REFUSING TO PROCEED: DEMO_OWNER_PASSWORD is required for E2E", file=sys.stderr)
        return 1

    backend_port = os.environ.get("E2E_BACKEND_PORT", DEFAULT_BACKEND_PORT)
    frontend_port = os.environ.get("E2E_FRONTEND_PORT", DEFAULT_FRONTEND_PORT)

    backend_env = os.environ.copy()
    backend_env["DATABASE_URL"] = e2e_database_url
    backend_env["ENVIRONMENT"] = "e2e"
    backend_env["NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED"] = "false"
    backend_env.setdefault("OPENAI_API_KEY", "sk-e2e-placeholder-not-a-real-key")
    backend_env.setdefault("JWT_SECRET_KEY", "e2e-local-only-placeholder-secret")
    backend_env["DEMO_OWNER_PASSWORD"] = demo_owner_password
    backend_env.setdefault("FRONTEND_URL", f"http://127.0.0.1:{frontend_port}")
    # M7 Slice 3C: Golden A browser E2E needs a deterministic AI response
    # (Founder Decision 3) - DECISION_CONTEXT_DEBUG feeds the fake client
    # the real reasoning reference catalog (see scripts/e2e_fake_ai_client.py)
    # and E2E_GOLDEN_MARKER is the one shared value tying the uploaded
    # fixture, the fake client's citation match, and the Playwright spec's
    # chat question together (see scripts/e2e_golden_fixture.py).
    backend_env["DECISION_CONTEXT_DEBUG"] = "true"
    backend_env["E2E_GOLDEN_MARKER"] = GOLDEN_MARKER
    backend_env["E2E_GOLDEN_HALL_NUMBER"] = GOLDEN_HALL_NUMBER

    frontend_env = os.environ.copy()
    frontend_env["NEXT_PUBLIC_AIMX_API_URL"] = f"http://127.0.0.1:{backend_port}"

    playwright_env = os.environ.copy()
    playwright_env["E2E_FRONTEND_PORT"] = frontend_port
    playwright_env["E2E_BACKEND_PORT"] = backend_port
    playwright_env["E2E_GOLDEN_MARKER"] = GOLDEN_MARKER
    golden_fixture_path = FRONTEND_DIR / "e2e" / "fixtures" / GOLDEN_FIXTURE_FILENAME
    playwright_env["E2E_GOLDEN_FIXTURE_PATH"] = str(golden_fixture_path)
    # Golden A logs in as the real seeded Jannat owner - propagate the exact
    # same environment-only DEMO_OWNER_PASSWORD validated above, so the
    # spec never needs (and must never contain) its own fallback or a
    # hardcoded password.
    playwright_env["DEMO_OWNER_PASSWORD"] = demo_owner_password

    print("[e2e] Building production frontend (NEXT_PUBLIC_AIMX_API_URL baked in now)...")
    try:
        run_frontend_build(frontend_env)
    except OrchestrationError as error:
        print(f"[e2e] {error}", file=sys.stderr)
        return 1

    print(f"[e2e] Running migrations against isolated E2E database on port {backend_port}...")
    try:
        run_migrations(backend_env)
    except OrchestrationError as error:
        print(f"[e2e] {error}", file=sys.stderr)
        return 1

    print("[e2e] Seeding Jannat Al-Firdaws into the isolated E2E database...")
    try:
        run_seed_jannat(backend_env)
        jannat_company_id = resolve_jannat_company_id(e2e_database_url)
    except OrchestrationError as error:
        print(f"[e2e] {error}", file=sys.stderr)
        return 1
    backend_env["JANNAT_COMPANY_ID"] = jannat_company_id
    print(f"[e2e] Jannat Al-Firdaws company_id resolved for this run: {jannat_company_id}")

    print(f"[e2e] Writing Golden A synthetic fixture workbook to {golden_fixture_path}...")
    write_golden_workbook(golden_fixture_path)

    backend_owned: OwnedProcess | None = None
    frontend_owned: OwnedProcess | None = None
    exit_code = 1
    cleanup_failed = False
    try:
        print(f"[e2e] Starting backend on 127.0.0.1:{backend_port}...")
        backend_owned = start_backend(backend_port, backend_env)
        wait_for_backend_health(backend_port, backend_owned)
        print("[e2e] Backend healthy.")

        print(f"[e2e] Starting production frontend on 127.0.0.1:{frontend_port}...")
        frontend_owned = start_frontend(frontend_port, frontend_env)
        wait_for_frontend_ready(frontend_port, frontend_owned)
        print("[e2e] Frontend ready. Launching Playwright (browser tests only, no server ownership)...")

        exit_code = run_playwright(playwright_env)
    except OrchestrationError as error:
        print(f"[e2e] {error}", file=sys.stderr)
        exit_code = 1
    finally:
        if frontend_owned is not None:
            print("[e2e] Stopping frontend...")
            frontend_stop = stop_owned_process(frontend_owned)
            print(f"[e2e] {frontend_stop.message}")
            if not frontend_stop.success:
                cleanup_failed = True
        if backend_owned is not None:
            print("[e2e] Stopping backend...")
            backend_stop = stop_owned_process(backend_owned)
            print(f"[e2e] {backend_stop.message}")
            if not backend_stop.success:
                cleanup_failed = True

    if cleanup_failed:
        print(
            "[e2e] Service cleanup could not be verified; treating the overall E2E result as a failure "
            "regardless of the browser test outcome.",
            file=sys.stderr,
        )

    return resolve_final_exit_code(exit_code, cleanup_failed)


if __name__ == "__main__":
    sys.exit(main())
