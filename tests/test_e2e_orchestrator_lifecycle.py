from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from scripts.e2e_orchestrator import (
    OrchestrationError,
    OwnedProcess,
    PlaywrightOutcome,
    build_frontend_build_command,
    build_frontend_start_command,
    build_playwright_command,
    resolve_final_exit_code,
    resolve_playwright_outcome,
    run_frontend_build,
    spawn_owned_process,
    stop_owned_process,
    wait_for_port_release,
    _wait_confirmed_exited,
    _wait_for_http_ready,
)


class FakeProcess:
    """Stand-in for subprocess.Popen exposing only what the orchestrator uses.

    Never spawns anything real, and `kill()` only records that it was
    called rather than touching any real machine process. `poll_sequence`/
    `wait_sequence` are consumed one call at a time; the last element
    repeats once exhausted, so a single-element sequence behaves like a
    fixed value.
    """

    def __init__(self, pid: int = 4242, poll_sequence=None, wait_sequence=None):
        self.pid = pid
        self.returncode: int | None = None
        self._poll_sequence = list(poll_sequence) if poll_sequence is not None else [None]
        self._wait_sequence = list(wait_sequence) if wait_sequence is not None else [0]
        self.wait_calls: list[float | None] = []
        self.kill_calls = 0

    def poll(self) -> int | None:
        value = self._poll_sequence[0] if len(self._poll_sequence) == 1 else self._poll_sequence.pop(0)
        self.returncode = value
        return value

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls.append(timeout)
        action = self._wait_sequence[0] if len(self._wait_sequence) == 1 else self._wait_sequence.pop(0)
        if isinstance(action, BaseException):
            raise action
        self.returncode = action
        return action

    def kill(self) -> None:
        self.kill_calls += 1


class FakeHttpResponse:
    def __init__(self, status: int = 200) -> None:
        self.status = status

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *args: object) -> bool:
        return False


# --- resolve_playwright_outcome (pure) --------------------------------------


def test_success_returns_zero_exit_code() -> None:
    outcome = resolve_playwright_outcome(returncode=0, timed_out=False)
    assert outcome == PlaywrightOutcome(exit_code=0, timed_out=False, message="Playwright run completed normally")


def test_failure_propagates_nonzero_exit_code() -> None:
    outcome = resolve_playwright_outcome(returncode=1, timed_out=False)
    assert outcome.exit_code == 1
    assert outcome.timed_out is False


def test_failure_preserves_exact_nonzero_exit_code() -> None:
    outcome = resolve_playwright_outcome(returncode=42, timed_out=False)
    assert outcome.exit_code == 42


def test_timeout_returns_nonzero_and_marks_timed_out() -> None:
    outcome = resolve_playwright_outcome(returncode=None, timed_out=True)
    assert outcome.exit_code != 0
    assert outcome.timed_out is True


def test_timeout_never_reports_as_success_even_if_returncode_later_supplied() -> None:
    outcome = resolve_playwright_outcome(returncode=0, timed_out=True)
    assert outcome.exit_code != 0
    assert outcome.timed_out is True


def test_missing_returncode_without_timeout_is_a_programming_error() -> None:
    with pytest.raises(ValueError):
        resolve_playwright_outcome(returncode=None, timed_out=False)


# --- direct CLI command construction, never npm/npx --------------------------


def test_frontend_build_command_uses_direct_node_and_next_cli_not_npm() -> None:
    command = build_frontend_build_command()
    assert command[0].lower().endswith(("node", "node.exe"))
    assert "build" in command
    joined = " ".join(command).lower()
    assert "npm" not in joined
    assert "npx" not in joined
    assert "next" in joined and "dist" in joined and "bin" in joined


def test_frontend_start_command_uses_direct_node_and_next_cli_not_npm() -> None:
    command = build_frontend_start_command("3100")
    assert command[0].lower().endswith(("node", "node.exe"))
    assert "start" in command
    assert "-p" in command and "3100" in command
    assert "-H" in command and "127.0.0.1" in command
    joined = " ".join(command).lower()
    assert "npm" not in joined
    assert "npx" not in joined


def test_playwright_command_uses_direct_node_and_playwright_cli_not_npx() -> None:
    command = build_playwright_command()
    assert command[0].lower().endswith(("node", "node.exe"))
    assert "test" in command
    joined = " ".join(command).lower()
    assert "npx" not in joined
    assert "npm" not in joined
    assert "playwright" in joined and "cli.js" in joined


# --- readiness polling ---------------------------------------------------------


def test_readiness_detects_early_process_death_without_any_http_call() -> None:
    dead = OwnedProcess(name="frontend", process=FakeProcess(poll_sequence=[1]))
    with pytest.raises(OrchestrationError, match="exited early"):
        _wait_for_http_ready("frontend", "http://127.0.0.1:9/nowhere", dead, timeout_seconds=5)


def test_readiness_returns_on_http_success() -> None:
    alive = OwnedProcess(name="frontend", process=FakeProcess(poll_sequence=[None]))
    with patch(
        "scripts.e2e_orchestrator.urllib.request.urlopen",
        return_value=FakeHttpResponse(200),
    ):
        _wait_for_http_ready("frontend", "http://127.0.0.1:9/login", alive, timeout_seconds=5)


# --- a single TimeoutExpired must never read as "exited" ---------------------


def test_wait_timeout_is_not_swallowed_as_success() -> None:
    stuck = FakeProcess(
        pid=7001,
        poll_sequence=[None],  # never actually exits when re-checked either
        wait_sequence=[subprocess.TimeoutExpired(cmd=["node"], timeout=10)],
    )
    assert _wait_confirmed_exited(stuck, timeout=10) is False


def test_wait_confirmed_exited_true_when_wait_returns_normally() -> None:
    finishes = FakeProcess(pid=7002, wait_sequence=[0])
    assert _wait_confirmed_exited(finishes, timeout=10) is True


# --- R4-UT-01/02/03/04/05: Windows handle-based root termination ------------


def test_r4_ut_01_and_02_live_root_is_killed_via_process_handle_and_verified() -> None:
    fake = FakeProcess(pid=6161, poll_sequence=[None], wait_sequence=[0])
    owned = OwnedProcess(name="backend", process=fake)

    with patch("scripts.e2e_orchestrator.subprocess.run") as mock_run:
        result = stop_owned_process(owned)

    assert fake.kill_calls == 1  # R4-UT-01: process.kill() called, not a spawned kill executable
    mock_run.assert_not_called()  # R4-UT-05: no taskkill (or anything else) spawned
    assert result.was_alive is True
    assert result.success is True  # R4-UT-02: kill + confirmed exit -> success
    assert "verified terminated" in result.message


def test_r4_ut_03_kill_plus_timeout_and_still_alive_is_a_verified_failure() -> None:
    stuck = FakeProcess(
        pid=6163,
        poll_sequence=[None],  # alive at the initial check AND at every re-check
        wait_sequence=[
            subprocess.TimeoutExpired(cmd=["node"], timeout=10),
            subprocess.TimeoutExpired(cmd=["node"], timeout=10),
        ],
    )
    owned = OwnedProcess(name="frontend", process=stuck)

    result = stop_owned_process(owned)

    assert stuck.kill_calls == 2  # one bounded retry, per the frozen "max 2 attempts" contract
    assert result.was_alive is True
    assert result.success is False
    assert "FAILED" in result.message
    assert "verified terminated" not in result.message


def test_r4_ut_04_already_dead_root_is_never_killed() -> None:
    fake = FakeProcess(pid=6164, poll_sequence=[0])
    owned = OwnedProcess(name="backend", process=fake)

    result = stop_owned_process(owned)

    assert fake.kill_calls == 0
    assert result.was_alive is False
    assert result.success is True


def test_r4_ut_05_no_taskkill_invocation_for_already_dead_root_either() -> None:
    fake = FakeProcess(pid=6165, poll_sequence=[0])
    owned = OwnedProcess(name="backend", process=fake)

    with patch("scripts.e2e_orchestrator.subprocess.run") as mock_run:
        stop_owned_process(owned)

    mock_run.assert_not_called()


# --- R4-UT-06/07: service port release is part of the cleanup contract -----


def test_r4_ut_06_root_killed_and_port_released_is_service_cleanup_success() -> None:
    fake = FakeProcess(pid=6166, poll_sequence=[None], wait_sequence=[0])
    owned = OwnedProcess(name="backend", process=fake, service_port=8100)

    with patch("scripts.e2e_orchestrator.wait_for_port_release", return_value=True) as mock_wait_port:
        result = stop_owned_process(owned)

    mock_wait_port.assert_called_once_with("127.0.0.1", 8100, pytest.approx(8.0))
    assert result.success is True
    assert "released" in result.message


def test_r4_ut_07_root_killed_but_port_still_listening_is_service_cleanup_failure() -> None:
    fake = FakeProcess(pid=6167, poll_sequence=[None], wait_sequence=[0])
    owned = OwnedProcess(name="frontend", process=fake, service_port=3100)

    with patch("scripts.e2e_orchestrator.wait_for_port_release", return_value=False):
        result = stop_owned_process(owned)

    assert result.success is False
    assert "still listening" in result.message
    assert "root process was verified terminated" in result.message  # root itself was fine


# --- R4-UT-08/09: cleanup failure still drives the overall E2E result ------


def test_r4_ut_08_cleanup_failure_flips_a_passing_result_nonzero() -> None:
    assert resolve_final_exit_code(playwright_exit_code=0, cleanup_failed=True) != 0


def test_r4_ut_09_browser_failure_stays_nonzero_regardless_of_cleanup() -> None:
    assert resolve_final_exit_code(playwright_exit_code=1, cleanup_failed=False) == 1
    assert resolve_final_exit_code(playwright_exit_code=1, cleanup_failed=True) == 1


def test_browser_success_with_verified_cleanup_stays_zero() -> None:
    assert resolve_final_exit_code(playwright_exit_code=0, cleanup_failed=False) == 0


def test_cleanup_failure_preserves_original_nonzero_code_rather_than_genericizing_it() -> None:
    assert resolve_final_exit_code(playwright_exit_code=42, cleanup_failed=True) == 42


# --- R4-UT-10: service stdio isolation (unchanged from Round 3) ------------


def test_r4_ut_10_isolated_service_spawn_does_not_inherit_parent_stdio(tmp_path) -> None:
    fake_popen = MagicMock(return_value=FakeProcess(pid=8001))
    with patch("scripts.e2e_orchestrator.subprocess.Popen", fake_popen):
        owned = spawn_owned_process(
            "backend", ["fake-backend"], cwd=tmp_path, env={}, isolate_stdio=True
        )
    try:
        _, kwargs = fake_popen.call_args
        assert kwargs.get("stdout") is not None
        assert kwargs.get("stderr") == subprocess.STDOUT
        assert owned.log_file is not None
    finally:
        if owned.log_file is not None:
            owned.log_file.close()


def test_non_isolated_spawn_leaves_stdio_inherited() -> None:
    fake_popen = MagicMock(return_value=FakeProcess(pid=8002))
    with patch("scripts.e2e_orchestrator.subprocess.Popen", fake_popen):
        owned = spawn_owned_process("playwright", ["fake-playwright"], cwd=".", env={})
    _, kwargs = fake_popen.call_args
    assert "stdout" not in kwargs
    assert "stderr" not in kwargs
    assert owned.log_file is None


# --- port-release helper (mocked socket checks, never real ports) ----------


def test_port_release_succeeds_immediately_when_already_free() -> None:
    with patch("scripts.e2e_orchestrator.is_port_listening", return_value=False) as mock_listen:
        assert wait_for_port_release("127.0.0.1", 3100, timeout_seconds=5) is True
    mock_listen.assert_called_once()


def test_port_release_succeeds_once_port_frees_up_before_deadline() -> None:
    with patch(
        "scripts.e2e_orchestrator.is_port_listening", side_effect=[True, True, False]
    ), patch("scripts.e2e_orchestrator.time.sleep", return_value=None):
        assert wait_for_port_release("127.0.0.1", 3100, timeout_seconds=5) is True


def test_port_release_fails_when_port_stays_occupied_through_deadline() -> None:
    with patch("scripts.e2e_orchestrator.is_port_listening", return_value=True), patch(
        "scripts.e2e_orchestrator.time.sleep", return_value=None
    ):
        assert wait_for_port_release("127.0.0.1", 3100, timeout_seconds=0.01) is False


# --- build timeout still triggers cleanup, now via the handle-based kill ---


def test_build_timeout_resolves_as_failure_and_triggers_verified_cleanup() -> None:
    # First wait() (the build's own bounded wait) times out; the subsequent
    # wait() inside stop_owned_process's kill-and-verify succeeds, simulating
    # a kill that actually worked.
    timing_out_then_killed = FakeProcess(
        pid=5150,
        poll_sequence=[None],
        wait_sequence=[subprocess.TimeoutExpired(cmd=["node"], timeout=300), 0],
    )
    owned = OwnedProcess(name="frontend-build", process=timing_out_then_killed)

    with patch("scripts.e2e_orchestrator.spawn_owned_process", return_value=owned):
        with pytest.raises(OrchestrationError, match="exceeded"):
            run_frontend_build(env={})
        assert timing_out_then_killed.kill_calls == 1


def test_build_nonzero_exit_without_timeout_is_a_failure() -> None:
    failed_process = FakeProcess(pid=5151, poll_sequence=[1], wait_sequence=[1])
    owned = OwnedProcess(name="frontend-build", process=failed_process)

    with patch("scripts.e2e_orchestrator.spawn_owned_process", return_value=owned):
        with pytest.raises(OrchestrationError, match="failed"):
            run_frontend_build(env={})
