"""Routing functions for the LangGraph workflow (conditional edges)."""

from langgraph.graph import END

from graph.state import AgentState


def route_after_input(state: AgentState):
    user_input = state.get("user_input")
    risk_score = state.get("risk_score", 0)

    # אם היוזר לא כתב כלום - עוצרים בכל מקרה
    if not user_input or not user_input.strip():
        return END

    # כאן נכנס המודל שלך לפעולה (אחרי שיש בקשה מהיוזר):
    if risk_score >= 0.2:
        print(f"--- Risk high ({risk_score:.2f}). Forwarding to researcher. ---")
        return "researcher"
    
    # אם היוזר ביקש אבל המודל אומר שהקוד בטוח (מתחת ל-0.2)
    print(f"--- Risk low ({risk_score:.2f}). Skipping deep research. ---")
    return END # או שאתה יכול להחליט לשלוח למסלול 'קל' יותר


def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "finish"


def route_after_cleaner(state: AgentState):
    if state.get("review_completed"):
        print("🔄 Cleaner -> Routing to WRITER")
        return "to_writer"
    print("🔄 Cleaner -> Routing to REVIEWER")
    return "to_reviewer"


def should_continue_after_test(state: AgentState):
    # 1. אם הטסט עבר - מסיימים בהצלחה
    if state.get("test_run_status") == "passed":
        print("✅ should_continue_after_test: PASSED. Finishing workflow.")
        return "finish"
    
    # 2. בדיקה כמה ניסיונות בוצעו עד כה
    # (מוודאים שהערך קיים, אם לא - מתייחסים כ-0)
    attempts = state.get("attempts", 0)
    max_attempts = 3 # ניתן לשנות לפי הצורך
    
    if attempts >= max_attempts:
        print(f"❌ should_continue_after_test: FAILED after {attempts} attempts. Stopping to prevent infinite loop.")
        return "finish" # או return "give_up" אם יש לך node כזה
    
    # 3. אם נכשל ויש עוד ניסיונות - ממשיכים לתיקון
    print(f"🔄 should_continue_after_test: FAILED. Attempt {attempts}/{max_attempts}. Routing to FIX_CODE.")
    return "fix_code"
