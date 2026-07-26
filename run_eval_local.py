"""
Local evaluation without CLI subcommands. Edit RUN, then:

    python run_eval_local.py
"""

from dotenv import load_dotenv

load_dotenv()

from shared.logging_config import configure_logging

configure_logging()

# --- edit for each run ---
RUN = "retrieval"  # "retrieval" | "rag"

from main import create_vector_db
from evaluation import run_rag_eval, run_retrieval_eval


def main() -> None:
    if RUN == "retrieval":
        vdb = create_vector_db()
        df = run_retrieval_eval(vdb, print_summary=True)
        if df is None:
            raise SystemExit(1)
    elif RUN == "rag":
        run_rag_eval()
    else:
        raise ValueError(f"Unknown RUN mode: {RUN!r} (use retrieval or rag)")


if __name__ == "__main__":
    main()
