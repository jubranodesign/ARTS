from evaluation.retrieval.datasets import test_set
from evaluation.retrieval.metrics import evaluate_retrieval
from services.vector_db_service import VectorDBService


def run_retrieval_suite(vdb: VectorDBService):
    """
    מריץ סדרת בדיקות על שכבת השליפה (Retrieval) של הפרויקט.
    """
    print("🚀 Starting Retrieval Evaluation Suite...\n")

    try:
        print(f"Evaluating {len(test_set)} queries against Semantic Search (K=5)...\n")
        results_df = evaluate_retrieval(test_set, vdb)

    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        return

    return results_df
