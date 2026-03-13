
from langgraph.graph.message import RemoveMessage
from graph.state import AgentState

def final_cleaner_writer(state: AgentState):

    all_messages = state.get("messages", [])

    # מחיקת כל ההודעות כדי להתחיל "דף חלק" לפני הריצה והתיקונים
    delete_messages = [RemoveMessage(id=m.id) for m in all_messages]
    
    return {
        "messages": delete_messages,
    }