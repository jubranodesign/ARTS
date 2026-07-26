import logging

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

from shared.embeddings import get_embeddings_model
from shared.llm_factory import get_model

logger = logging.getLogger(__name__)


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
    logger.debug("extracted_contexts: %s", extracted_contexts)
    logger.debug("final_dump: %s", final_dump)
    logger.debug("ground_truth: %s", ground_truth)
    logger.debug("question: %s", question)
    logger.debug("message_history: %s", message_history)

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
    
    logger.info("Starting Evaluation Suite on %s results...", len(results_to_evaluate))

    for i, item in enumerate(results_to_evaluate):
        logger.info(
            "Judging case %s/%s: %s",
            i + 1,
            len(results_to_evaluate),
            item['question'],
        )
        
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

    logger.info("Evaluation Suite finished.")
    return batch_scores
