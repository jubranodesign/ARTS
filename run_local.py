"""
Local dev entry without CLI. Set RUN and related flags, then:

    python run_local.py
"""

from dotenv import load_dotenv

load_dotenv()

from shared.logging_config import configure_logging

configure_logging()

# --- edit for each run ---
RUN = "agent"  # "ingest" | "agent" | "both"
INGEST_MODE = "both"  # "both" | "seed" | "source" — used when RUN is "ingest" or "both"
USE_INVOKE = False  # used when RUN is "agent" or "both"
REPO_PATH = None  # None → REPO_PATH from .env via get_repo_path()
USER_TASK = None  # None → USER_TASK env or DEFAULT_USER_TASK in shared/constants.py
GRAPH_CONFIG: dict | None = None  # e.g. {"model_provider": "mistral", "thread_id": "dev-1"}

from shared.paths import get_repo_path
from main import run_agent_only, run_ingest_only, run_pipeline


def main() -> None:
    repo_path = REPO_PATH or get_repo_path()

    if RUN == "ingest":
        run_ingest_only(repo_path, INGEST_MODE)
    elif RUN == "agent":
        run_agent_only(
            repo_path,
            invoke=USE_INVOKE,
            user_task=USER_TASK,
            configurable=GRAPH_CONFIG,
        )
    elif RUN == "both":
        run_pipeline(
            repo_path,
            ingest=INGEST_MODE,
            invoke=USE_INVOKE,
            user_task=USER_TASK,
            configurable=GRAPH_CONFIG,
        )
    else:
        raise ValueError(f"Unknown RUN mode: {RUN!r} (use ingest, agent, or both)")


if __name__ == "__main__":
    main()
