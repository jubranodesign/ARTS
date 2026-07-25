import logging

from evaluation.retrieval.datasets import test_set
from evaluation.retrieval.metrics import evaluate_retrieval
from services.vector_db_service import VectorDBService

logger = logging.getLogger(__name__)


def run_retrieval_suite(vdb: VectorDBService):
    """
    מריץ סדרת בדיקות על שכבת השליפה (Retrieval) של הפרויקט.
    """
    logger.info("Starting Retrieval Evaluation Suite...")

    try:
        logger.info(
            "Evaluating %s queries against Semantic Search (K=5)...",
            len(test_set),
        )
        results_df = evaluate_retrieval(test_set, vdb)

    except Exception as e:
        logger.error("Error during evaluation: %s", e)
        return

    return results_df
