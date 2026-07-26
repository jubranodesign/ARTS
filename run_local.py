"""
Local dev entry without CLI. Set RUN and related flags, then:

    python run_local.py
"""

from dotenv import load_dotenv

load_dotenv()

from shared.logging_config import configure_logging

configure_logging()

# --- edit for each run ---
RUN = "ingest"  # "ingest" | "agent" | "both"
INGEST_MODE = "both"  # "both" | "seed" | "source" — used when RUN is "ingest" or "both"
REPO_PATH = None  # None → REPO_PATH from .env via get_repo_path()
USER_TASK = None  # None → USER_TASK env or DEFAULT_USER_TASK in shared/constants.py
GRAPH_CONFIG: dict | None = None  # optional: thread_id, model_provider — see shared/graph_config.py

from shared.paths import get_repo_path
from shared.startup_checks import validate_runtime_startup
from main import create_vector_db, run_agent_only, run_ingest_only, run_pipeline


def main() -> None:
    repo_path = REPO_PATH or get_repo_path()
    warn_empty_vdb = RUN == "agent"
    validate_runtime_startup(repo_path, warn_empty_vdb=warn_empty_vdb)
    vdb = create_vector_db()

    if RUN == "ingest":
        run_ingest_only(repo_path, INGEST_MODE, vdb)
    elif RUN == "agent":
        run_agent_only(
            repo_path,
            vdb,
            user_task=USER_TASK,
            configurable=GRAPH_CONFIG,
        )
    elif RUN == "both":
        run_pipeline(
            repo_path,
            vdb,
            ingest=INGEST_MODE,
            user_task=USER_TASK,
            configurable=GRAPH_CONFIG,
        )
    else:
        raise ValueError(f"Unknown RUN mode: {RUN!r} (use ingest, agent, or both)")


if __name__ == "__main__":
    main()
