import os
from evaluation.retrieval.datasets import test_set
from evaluation.retrieval.metrics import evaluate_retrieval
from services.vector_db_service import VectorDBService

def run_retrieval_suite(vdb=None):
    """
    מריץ סדרת בדיקות על שכבת השליפה (Retrieval) של הפרויקט.
    """
    print("🚀 Starting Retrieval Evaluation Suite...\n")

    # 1. התחברות ל-Vector Store הקיים שלך
    # וודא שהפונקציה הזו מחזירה את ה-vstore המאופלח של Chroma
    vstore = vdb or VectorDBService()

    # 3. הרצת ההערכה
    try:
        print(f"Evaluating {len(test_set)} queries against Semantic Search (K=5)...\n")
        results_df = evaluate_retrieval(test_set, vstore)
        
        # 4. שמירת התוצאות לתיעוד (אופציונלי - מעולה לפרויקט גמר)
        # results_df.to_csv("evaluation/retrieval/results_last_run.csv")
        # print("\n✅ Results saved to evaluation/retrieval/results_last_run.csv")

    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
