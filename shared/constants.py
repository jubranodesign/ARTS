import os

TEST_FRAMEWORK = "pytest"
MOCK_TOOL = "unittest.mock"

LLM_MODEL_NAME = "gemini-2.5-flash"

DEFAULT_USER_TASK = "Write unit tests for the file analysis_service/analysis.py"


def resolve_user_task(override: str | None = None) -> str:
    """CLI/run_local override, then USER_TASK env, then DEFAULT_USER_TASK."""
    if override is not None and str(override).strip():
        return str(override).strip()
    env_task = os.getenv("USER_TASK")
    if env_task and str(env_task).strip():
        return str(env_task).strip()
    return DEFAULT_USER_TASK
