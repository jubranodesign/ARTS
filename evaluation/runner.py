"""Public evaluation runners (retrieval + RAG)."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from services.vector_db_service import VectorDBService


def run_retrieval_eval(
    vdb: "VectorDBService | None" = None,
    *,
    repo_path: str | None = None,
    skip_startup_checks: bool = False,
    print_summary: bool = True,
) -> "pd.DataFrame | None":
    """
    Run semantic retrieval metrics (evaluation/retrieval/datasets.py).

    Pass an existing ``vdb`` after ingest, or leave None to create ``VectorDBService()``.
    """
    from evaluation.retrieval.eval_utils import run_retrieval_suite
    from services.vector_db_service import VectorDBService
    from shared.paths import get_repo_path
    from shared.startup_checks import validate_runtime_startup

    resolved_repo = repo_path or get_repo_path()
    if not skip_startup_checks:
        validate_runtime_startup(resolved_repo, warn_empty_vdb=True)

    vdb_instance = vdb or VectorDBService()
    df = run_retrieval_suite(vdb_instance)
    if df is not None and print_summary:
        print("\n--- Retrieval summary ---")
        print(df.to_string())
        print("\n--- Averages ---")
        print(df.mean(numeric_only=True).to_string())
    return df


def run_rag_eval(*, skip_startup_checks: bool = False) -> list:
    """
    Run Ragas on the bundled sample (evaluation/rag/researcher_agent/datasets.py).

    Requires: pip install -e \".[eval]\"
    """
    from shared.paths import get_repo_path
    from shared.startup_checks import check_llm_provider_configured, check_repo_path_exists

    if not skip_startup_checks:
        check_repo_path_exists(get_repo_path())
        check_llm_provider_configured()

    try:
        from evaluation.rag.researcher_agent.run_eval import run_rag_offline_eval
    except ImportError as exc:
        raise RuntimeError(
            'RAG evaluation requires optional deps. Install with: pip install -e ".[eval]"'
        ) from exc

    return run_rag_offline_eval()


def main(argv: list[str] | None = None) -> int:
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

    args = parser.parse_args(argv)
    if args.mode == "retrieval":
        df = run_retrieval_eval()
        return 0 if df is not None else 1
    if args.mode == "rag":
        try:
            run_rag_eval()
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0
    return 2
