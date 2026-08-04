import subprocess
import sys
from typing import Tuple

from shared.repo_language import is_python_pipeline


def run_pytest(
    full_path: str,
    repo_path: str,
    env: dict[str, str] = None,
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
    """
    Run tests via BYOR runner (ARTS_TEST_RUNNER or REPO_PATH/.arts/runner.py),
    or built-in pytest when REPO_LANGUAGE is python and no runner is configured.
    """
    from utils.runner_loader import resolve_test_runner

    runner = resolve_test_runner(repo_path)
    if runner is not None:
        return runner(
            full_path,
            repo_path,
            env=env,
            timeout=timeout,
        )

    if not is_python_pipeline():
        return (
            "failed",
            "No test runner configured for non-Python REPO_LANGUAGE. "
            "Set ARTS_TEST_RUNNER=module:callable or add REPO_PATH/.arts/runner.py",
        )

    return run_pytest(full_path, repo_path, env=env, timeout=timeout)
