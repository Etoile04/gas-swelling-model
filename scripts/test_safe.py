#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str]) -> tuple[int, list[str]]:
    parser = argparse.ArgumentParser(
        description="Run pytest with a timeout and process-tree cleanup."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds. Defaults to TEST_TIMEOUT_SECONDS or 1200.",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to pytest.",
    )

    parsed = parser.parse_args(argv[1:])
    pytest_args = parsed.pytest_args or ["tests/", "-v"]
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]

    timeout_seconds = parsed.timeout
    if timeout_seconds is None:
        timeout_seconds = int(os.environ.get("TEST_TIMEOUT_SECONDS", "1200"))

    return timeout_seconds, pytest_args


def resolve_python_and_pytest() -> tuple[str, list[str]]:
    posix_venv_python = ROOT_DIR / ".venv" / "bin" / "python"
    posix_venv_pytest = ROOT_DIR / ".venv" / "bin" / "pytest"
    windows_venv_python = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    windows_venv_pytest = ROOT_DIR / ".venv" / "Scripts" / "pytest.exe"

    if posix_venv_python.exists() and posix_venv_pytest.exists():
        return str(posix_venv_python), [str(posix_venv_pytest)]
    if windows_venv_python.exists() and windows_venv_pytest.exists():
        return str(windows_venv_python), [str(windows_venv_pytest)]

    python_bin = shutil.which("python")
    if python_bin:
        return python_bin, [python_bin, "-m", "pytest"]

    raise SystemExit("error: no usable python interpreter found")


def kill_process_tree(proc: subprocess.Popen[bytes], sigterm_timeout: int = 10) -> int:
    if os.name == "nt":
        try:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        except Exception:
            proc.terminate()
        try:
            return proc.wait(timeout=sigterm_timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            return proc.wait()

    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return proc.poll() or 0

    try:
        return proc.wait(timeout=sigterm_timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return proc.wait()


def main(argv: list[str]) -> int:
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    timeout_seconds, pytest_args = parse_args(argv)

    python_bin, pytest_prefix = resolve_python_and_pytest()
    cmd = [*pytest_prefix, *pytest_args]

    print(f"[test_safe] timeout={timeout_seconds}s", flush=True)
    print(f"[test_safe] python={python_bin}", flush=True)
    print(f"[test_safe] command={' '.join(cmd)}", flush=True)

    kwargs: dict[str, object] = {"cwd": str(ROOT_DIR)}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(cmd, **kwargs)

    def handle_signal(signum: int, _frame: object) -> None:
        print(f"[test_safe] received signal {signum}, terminating pytest process tree", flush=True)
        rc = kill_process_tree(proc)
        raise SystemExit(rc if rc != 0 else 128 + signum)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        return proc.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        print(f"[test_safe] timeout after {timeout_seconds}s, terminating pytest process tree", flush=True)
        return kill_process_tree(proc)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
