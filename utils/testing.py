import subprocess
import sys
from typing import Tuple


def run_pytest(
    full_path: str,
    repo_path: str,
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

