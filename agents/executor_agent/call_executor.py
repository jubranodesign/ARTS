import logging
import os

from langgraph.graph.state import RunnableConfig

from graph.state import AgentState
from shared.paths import get_safe_full_path
from shared.repo_language import is_python_pipeline
from utils.testing import run_tests

logger = logging.getLogger(__name__)


def call_executor(state: AgentState, config: RunnableConfig):
    repo_path = config["configurable"]["repo_path"]
    test_file_path = state.get("test_file_path")
    current_attempts = state.get("attempts", 0)
    target_file = state.get("target_file")

    if not test_file_path:
        logger.error("No test file path found in state.")
        return {"test_run_status": "failed", "last_run_logs": "No test file path provided."}

    logger.info("Running tests on: %s", test_file_path)

    env = os.environ.copy()

    if is_python_pipeline() and target_file:
        source_service_dir = os.path.dirname(target_file)
        full_service_path = os.path.abspath(os.path.join(repo_path, source_service_dir))
        path_separator = ";" if os.name == "nt" else ":"
        env["PYTHONPATH"] = (
            f"{repo_path}{path_separator}{full_service_path}"
            f"{path_separator}{env.get('PYTHONPATH', '')}"
        )
        logger.info("Injected PYTHONPATH entry: %s", full_service_path)

    full_test_file_path = get_safe_full_path(repo_path, test_file_path)
    logger.info("Test file full path: %s", full_test_file_path)

    status, logs = run_tests(
        full_path=full_test_file_path,
        repo_path=repo_path,
        env=env,
        timeout=60,
    )

    return {
        "test_run_status": status,
        "last_run_logs": logs,
        "attempts": current_attempts + 1,
    }
