from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas import evaluate
from datasets import Dataset

from shared.config import get_embeddings_model, get_model

def evaluate_quality(question, final_dump, message_history, ground_truth):
    """
    final_dump: ה-RESEARCH_DATA_DUMP האחרון שהסוכן הוציא.
    message_history: ה-trimmed_history המלא (כולל ה-Tool Outputs).
    ground_truth: הציפייה שלך מהמהנדס.
    """

    # 1. חילוץ ה-Chunks מתוך ה-Tool Messages בהיסטוריה
    # אנחנו מחפשים הודעות שהן פלט של כלי החיפוש (ToolMessage)
    extracted_contexts = [
        msg.content for msg in message_history 
        if getattr(msg, 'type', '') == 'tool'
    ]
    print(f"extracted_contexts: {extracted_contexts}")
    print(f"final_dump: {final_dump}")
    print(f"ground_truth: {ground_truth}")
    print(f"question: {question}")
    print(f"message_history: {message_history}")

    # 2. בניית ה-Sample ל-Ragas
    sample = {
        "question": [question],
        "contexts": [extracted_contexts], # כל מה שהחוקר "קרא" מה-DB
        "answer": [final_dump],           # מה שהחוקר "סיכם" בסוף
        "ground_truth": [ground_truth]    # המציאות האובייקטיבית
    }
    
    dataset = Dataset.from_dict(sample)
    
    # 3. הרצת המדדים
    result = evaluate(
    dataset, 
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    llm=get_model(),
    embeddings=get_embeddings_model()
    )
    return result


def run_evaluation_suite(results_to_evaluate):
    """
    מקבלת רשימה של תוצאות שכבר הורצו ומפעילה עליהן אבחון בלולאה.
    
    כל פריט ב-results_to_evaluate צריך להיות dict במבנה:
    {
        "question": "...",
        "final_dump": "...",        # הפלט האחרון של הסוכן
        "message_history": [...],   # רשימת ההודעות (כולל ToolMessages)
        "ground_truth": "..."       # הציפייה שלך
    }
    """
    batch_scores = []
    
    print(f"📊 Starting Evaluation Suite on {len(results_to_evaluate)} results...")
    print("-" * 50)

    for i, item in enumerate(results_to_evaluate):
        print(f"⚖️ Judging Case {i+1}/{len(results_to_evaluate)}: {item['question']}")
        
        # שימוש בפונקציה הקיימת שלך על כל פריט ברשימה
        result = evaluate_quality(
            question=item['question'],
            final_dump=item['final_dump'],
            message_history=item['message_history'],
            ground_truth=item['ground_truth']
        )
        
        # איסוף התוצאות
        batch_scores.append({
            "case": i + 1,
            "question": item['question'],
            "scores": result
        })

    print("\n✅ Evaluation Suite Finished.")
    return batch_scores