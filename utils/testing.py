import subprocess
import sys
from typing import Tuple

from shared.repo_language import effective_repo_language


def run_pytest(
    full_path: str,
    repo_path: str,
    env: dict[str, str] = None,  # <--- הגדרת הטיפוס כאן
    timeout: int = 60,
) -> Tuple[str, str]:
    """
    Executes pytest in a stable way (easy to unit-test via mocking subprocess.run).

    Returns:
        (status, logs)
        status: "passed" | "failed"
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", full_path, "--tb=short"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )

        if result.returncode == 0:
            return "passed", result.stdout

        # Combine stdout + stderr so the model/agent sees full context.
        return "failed", (result.stdout + "\n" + result.stderr)

    except subprocess.TimeoutExpired:
        return (
            "failed",
            "Timeout: Pytest execution took too long (possible infinite loop).",
        )
    except Exception as e:
        return "failed", f"Execution Error: {str(e)}"


def run_tests(
    full_path: str,
    repo_path: str,
    env: dict[str, str] | None = None,
    timeout: int = 60,
    *,
    language: str | None = None,
) -> Tuple[str, str]:
    """Run tests for the configured repo language (python only today)."""
    effective_repo_language()
    return run_pytest(full_path, repo_path, env=env, timeout=timeout)

