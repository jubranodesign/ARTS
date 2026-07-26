"""Run offline RAG (Ragas) evaluation on the bundled researcher sample."""

from __future__ import annotations

import logging

from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)


def _sample_to_eval_item(sample: dict) -> dict:
    """Map datasets.sample to run_evaluation_suite item (tool outputs as context)."""
    contexts = sample.get("contexts") or []
    history = [
        ToolMessage(
            content=str(ctx),
            tool_call_id=f"eval-ctx-{i}",
            name="search_source_code_semantic",
        )
        for i, ctx in enumerate(contexts)
    ]
    return {
        "question": sample["question"],
        "final_dump": sample["answer"],
        "message_history": history,
        "ground_truth": sample["ground_truth"],
    }


def run_rag_offline_eval() -> list:
    """
    Evaluate the researcher RAG sample in evaluation/rag/researcher_agent/datasets.py.
    Requires: pip install -e \".[eval]\" (ragas).
    """
    try:
        from evaluation.rag.eval_utils import run_evaluation_suite
    except ImportError as exc:
        raise RuntimeError(
            "RAG evaluation requires optional deps. Install with: pip install -e \".[eval]\""
        ) from exc

    from evaluation.rag.researcher_agent.datasets import sample

    item = _sample_to_eval_item(sample)
    results = run_evaluation_suite([item])
    for row in results:
        logger.info("RAG scores for %r: %s", row["question"], row["scores"])
    return results
