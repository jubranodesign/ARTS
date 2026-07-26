from langchain_core.prompts import ChatPromptTemplate

from typing import Type
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate

from shared.llm_factory import get_model

def evaluate_with_custom_judge(
    judgment_model: Type[BaseModel], 
    rubric: str, 
    question: str, 
    answer: str, 
    message_history: list,
    llm = None  # פרמטר אופציונלי
):
    """
    מנוע שיפוט שמריץ אבחון לפי סכימה ורובריקה.
    משתמש ב-get_model() כברירת מחדל.
    """
    # אם לא הועבר מודל ספציפי, נשתמש בברירת המחדל של הפרויקט
    judge_llm = llm if llm is not None else get_model()

    # 1. חילוץ Context (הודעות הכלים מההיסטוריה)
    context = "\n---\n".join([
        msg.content for msg in message_history 
        if getattr(msg, 'type', '') == 'tool'
    ])

    # 2. חיבור לסכימה המבוקשת (Structured Output)
    structured_llm = judge_llm.with_structured_output(judgment_model)

    # 3. בניית הפרומפט המקצועי
    prompt = ChatPromptTemplate.from_messages([
        (
            "system", 
            "You are a strict technical auditor responsible for ensuring AI agents follow protocol. "
            "Your judgment must be binary and evidence-based. Do not offer constructive feedback, only a cold audit. "
            "\n\n### AUDIT RUBRIC:\n{rubric}"
        ),
        (
            "human", 
            "### DATA TO AUDIT:\n"
            "- USER_QUESTION: {question}\n"
            "- CONTEXT (Tools): {context}\n"
            "- AGENT_ANSWER: {answer}\n\n"
            "Produce the structured audit report now."
        )
    ])

    # 4. ביצוע האבחון
    chain = prompt | structured_llm
    return chain.invoke({
        "question": question,
        "context": context,
        "answer": answer,
        "rubric": rubric  
    })