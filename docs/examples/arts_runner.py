"""
Example BYOR test runner for REPO_PATH/.arts/runner.py

Copy to: <your-repo>/.arts/runner.py and adapt the command.

Contract:
    run_tests(full_test_path, repo_path, env=None, timeout=60) -> tuple[str, str]
    status is "passed" or "failed"; logs is stdout/stderr text for the repair agent.
"""

from __future__ import annotations

import subprocess
import sys


def run_tests(full_test_path, repo_path, env=None, timeout=60):
    """Default example: pytest (Python repos). Replace with jest, mvn test, etc."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", full_test_path, "--tb=short"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    logs = (result.stdout or "") + "\n" + (result.stderr or "")
    status = "passed" if result.returncode == 0 else "failed"
    return status, logs
