"""
CLI shim (same as ``python -m evaluation``).

Prefer programmatic use::

    from evaluation import run_retrieval_eval, run_rag_eval
"""

from dotenv import load_dotenv

load_dotenv()

from shared.logging_config import configure_logging

configure_logging()

from evaluation.runner import main, run_rag_eval, run_retrieval_eval

__all__ = ["main", "run_rag_eval", "run_retrieval_eval"]

if __name__ == "__main__":
    raise SystemExit(main())
