"""
Local dev entry: ingest + agent without CLI. Edit the flags below, then:

    python run_local.py
"""

from dotenv import load_dotenv

load_dotenv()

from shared.logging_config import configure_logging

configure_logging()

# --- edit for each run ---
DO_INGEST = True
INGEST_MODE = "both"  # "both" | "seed" | "source" (ignored when DO_INGEST is False)
USE_INVOKE = False
REPO_PATH = None  # None → REPO_PATH from .env via get_repo_path()

from shared.paths import get_repo_path
from main import run_pipeline


def main() -> None:
    repo_path = REPO_PATH or get_repo_path()
    ingest = INGEST_MODE if DO_INGEST else None
    run_pipeline(repo_path, ingest=ingest, invoke=USE_INVOKE)


if __name__ == "__main__":
    main()
