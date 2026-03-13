from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph.state import RunnableConfig
from agents.designer_agent.prompts import DESIGNER_PROMPT_TEMPLATE
from agents.designer_agent.tools import DESIGNER_TOOLS
from graph.state import AgentState
from shared.config import setup_node_llm
from utils.utils import get_trimmed_messages

def call_designer(state: AgentState, config: RunnableConfig):

    llm = setup_node_llm(config, DESIGNER_TOOLS)

    # 1. שליפת נתונים
    architecture_summary = state.get("architecture_summary", "No summary available")
    investigated_files = state.get("investigated_files", [])
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])

    # 2. בניית ה-Prompt (כ-System)
    enriched_prompt = DESIGNER_PROMPT_TEMPLATE.format(
        architecture_summary=architecture_summary,
        investigated_files=investigated_files,
        user_input=user_input
    )
    system_msg = SystemMessage(content=enriched_prompt)

    # 3. ניקוי היסטוריה (ללא System ישנים)
    clean_history = [m for m in messages if not isinstance(m, SystemMessage)]
    
    # 4. גזירה (Trim)
    trimmed_history = get_trimmed_messages(clean_history, llm, max_tokens=4000)

    # --- התיקון הקריטי כאן ---
    # ג'מיני חייב לראות HumanMessage כדי להבין למי הוא עונה.
    # אם ההיסטוריה מתחילה ב-AI (כי מחקנו את ה-Human המקורי), נזריק הודעת פתיחה.
    
    user_trigger = HumanMessage(content=f"Instruction: Design tests for the following request: {user_input}")

    # הרכבת הרשימה בסדר שג'מיני אוהב:
    # System -> Human (הטריגר) -> השאר (AI, Tool וכו')
    messages_to_send = [system_msg, user_trigger] + trimmed_history

    # בדיקת דיבאג נוספת
    print(f"DEBUG: Final Messages types: {[type(m) for m in messages_to_send]}")

    try:
        response = llm.invoke(messages_to_send)
        return {"messages": [response]}
    except Exception as e:
        print(f"❌ Designer LLM Error: {e}")
        raise e