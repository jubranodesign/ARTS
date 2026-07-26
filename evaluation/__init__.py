"""Offline evaluation package (retrieval metrics, RAG/Ragas)."""

from evaluation.runner import main, run_rag_eval, run_retrieval_eval

__all__ = [
    "main",
    "run_rag_eval",
    "run_retrieval_eval",
]
