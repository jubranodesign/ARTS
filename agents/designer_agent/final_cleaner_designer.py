
import re
from langgraph.graph.message import RemoveMessage
from graph.state import AgentState

def final_cleaner_designer(state: AgentState):

    # 3. שליפת תוכנית הבדיקות (מההודעה האחרונה של ה-Reviewer)
    all_messages = state.get("messages", [])
    final_plan = all_messages[-1].content if all_messages else ""

    # 4. מחיקת היסטוריית ההודעות (RemoveMessage)
    delete_messages = [RemoveMessage(id=m.id) for m in all_messages]

    return {
        "test_plan": final_plan,
        "messages": delete_messages
    }