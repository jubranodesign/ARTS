
import logging
import re
from langgraph.graph.message import RemoveMessage
from graph.state import AgentState
from utils.utils import get_clean_text

logger = logging.getLogger(__name__)

def final_cleaner_designer(state: AgentState):
    all_messages = state.get("messages", [])
    
    if not all_messages:
        return {"test_plan": state.get("test_plan", ""), "messages": []}

    # 1. שליפת התוכן מההודעה האחרונה (Designer או Reviewer)
    # שימוש ב-get_clean_text כדי לטפל במבנה של ג'מיני/Qwen
    raw_content = all_messages[-1].content
    final_plan = get_clean_text(raw_content)

    # 2. זיהוי האם זו הודעה מה-Reviewer (לצורך ניתוב בגרף)
    # אנחנו בודקים אם יש מילות מפתח של ה-Reviewer בטקסט
    is_review = "Review Notes" in final_plan or "Final Test Plan" in final_plan

    # 3. מחיקת היסטוריית ההודעות (מנקים את ה-Context)
    delete_messages = [RemoveMessage(id=m.id) for m in all_messages if m.id]

    logger.info("Cleaner: saved content to test_plan; messages cleared")

    return {
        "test_plan": final_plan,
        "messages": delete_messages,
        "review_completed": is_review  # דגל לטובת ה-Conditional Edge
    }