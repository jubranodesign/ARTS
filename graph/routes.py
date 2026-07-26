"""Routing functions for the LangGraph workflow (conditional edges)."""

import logging

from langgraph.graph import END

from graph.state import AgentState
from shared.run_policy import get_max_test_attempts, get_risk_threshold

logger = logging.getLogger(__name__)


def route_after_input(state: AgentState):
    user_input = state.get("user_input")
    risk_score = state.get("risk_score", 0)

    # אם היוזר לא כתב כלום - עוצרים בכל מקרה
    if not user_input or not user_input.strip():
        return END

    threshold = get_risk_threshold()
    if risk_score >= threshold:
        logger.info(
            "Risk high (%.2f >= %.2f). Forwarding to researcher.",
            risk_score,
            threshold,
        )
        return "researcher"

    logger.info(
        "Risk low (%.2f < %.2f). Ending workflow (no researcher/writer path).",
        risk_score,
        threshold,
    )
    return END # או שאתה יכול להחליט לשלוח למסלול 'קל' יותר


def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "finish"


def route_after_cleaner(state: AgentState):
    if state.get("review_completed"):
        logger.info("Cleaner -> routing to WRITER")
        return "to_writer"
    logger.info("Cleaner -> routing to REVIEWER")
    return "to_reviewer"


def should_continue_after_test(state: AgentState):
    # 1. אם הטסט עבר - מסיימים בהצלחה
    if state.get("test_run_status") == "passed":
        logger.info("should_continue_after_test: PASSED. Finishing workflow.")
        return "finish"
    
    # 2. בדיקה כמה ניסיונות בוצעו עד כה
    # (מוודאים שהערך קיים, אם לא - מתייחסים כ-0)
    attempts = state.get("attempts", 0)
    max_attempts = get_max_test_attempts()

    if attempts >= max_attempts:
        logger.error(
            "should_continue_after_test: FAILED after %s attempts. Stopping to prevent infinite loop.",
            attempts,
        )
        return "finish" # או return "give_up" אם יש לך node כזה
    
    # 3. אם נכשל ויש עוד ניסיונות - ממשיכים לתיקון
    logger.info(
        "should_continue_after_test: FAILED. Attempt %s/%s. Routing to FIX_CODE.",
        attempts,
        max_attempts,
    )
    return "fix_code"
