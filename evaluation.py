"""
Offline evaluation CLI (not used by the live LangGraph agent).

  python evaluation.py retrieval   # Chroma semantic retrieval metrics
  python evaluation.py rag         # Ragas on bundled researcher sample (needs .[eval])
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

from shared.logging_config import configure_logging

configure_logging()


def _run_retrieval() -> int:
    from evaluation.retrieval.eval_utils import run_retrieval_suite
    from services.vector_db_service import VectorDBService
    from shared.paths import get_repo_path
    from shared.startup_checks import validate_runtime_startup

    repo_path = get_repo_path()
    validate_runtime_startup(repo_path, warn_empty_vdb=True)

    vdb = VectorDBService()
    df = run_retrieval_suite(vdb)
    if df is None:
        return 1
    print("\n--- Retrieval summary ---")
    print(df.to_string())
    print("\n--- Averages ---")
    print(df.mean(numeric_only=True).to_string())
    return 0


def _run_rag() -> int:
    from shared.paths import get_repo_path
    from shared.startup_checks import check_llm_provider_configured, check_repo_path_exists

    repo_path = get_repo_path()
    check_repo_path_exists(repo_path)
    check_llm_provider_configured()

    try:
        from evaluation.rag.researcher_agent.run_eval import run_rag_offline_eval
    except ImportError as exc:
        print(
            "RAG evaluation requires optional dependencies:\n"
            '  pip install -e ".[eval]"',
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    run_rag_offline_eval()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline evaluation: retrieval (Chroma) or RAG (Ragas sample)."
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    sub.add_parser(
        "retrieval",
        help="Run semantic retrieval metrics on evaluation/retrieval/datasets.py (needs ingest).",
    )
    sub.add_parser(
        "rag",
        help="Run Ragas on evaluation/rag/researcher_agent/datasets.py sample.",
    )

    args = parser.parse_args()
    if args.mode == "retrieval":
        raise SystemExit(_run_retrieval())
    if args.mode == "rag":
        raise SystemExit(_run_rag())
    raise SystemExit(2)


if __name__ == "__main__":
    main()
