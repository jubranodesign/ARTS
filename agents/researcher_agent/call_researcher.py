from langchain_core.messages import SystemMessage
from langgraph.graph.state import RunnableConfig
from agents.researcher_agent.prompts import RESEARCHER_SYSTEM_PROMPT
from agents.researcher_agent.tools import RESEARCHER_TOOLS
from graph.state import AgentState
from shared.config import setup_node_llm
from utils.utils import extract_python_path, get_trimmed_messages

# הצמדת הכלים למופע המשותף

def call_researcher(state: AgentState, config: RunnableConfig):

    llm = setup_node_llm(config, RESEARCHER_TOOLS)

    user_input = state.get("user_input", "")
    target_file = extract_python_path(user_input)
    
    # 1. שליפת נתונים - אנחנו סומכים על ה-main שהזין HumanMessage
    current_summary = state.get("architecture_summary", "No summary available yet.")
    user_task = state.get("user_input", "No task defined.")
    all_messages = state.get("messages", [])

    # 2. בניית ה-System Message המעודכן
    # ה-user_task נשאר כאן כי הוא קריטי להנחיית המודל בכל סיבוב
    instruction_content = f"""{RESEARCHER_SYSTEM_PROMPT}

Target Task: {user_task}
Current Architecture Knowledge: {current_summary}
"""
    system_msg = SystemMessage(content=instruction_content)

    # 3. סינון היסטוריה - משאירים רק Human, AI ו-Tool
    # אנחנו מעיפים את ה-SystemMessage הקודם כדי שג'מיני לא יתבלבל מהסדר
    clean_history = [m for m in all_messages if not isinstance(m, SystemMessage)]
    
    # 4. גזירה (Trim) למניעת חריגת טוקנים
    trimmed_history = get_trimmed_messages(clean_history, llm, max_tokens=4000)

    # 5. בניית הרשימה הסופית: [System, Human (מה-main), AI, Tool...]
    messages_to_send = [system_msg] + trimmed_history

    # 6. קריאה למודל
    try:
        response = llm.invoke(messages_to_send)
        return {
            "messages": [response],
            "target_file": target_file, 
            }
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        # הדפסת סדר ההודעות לדיבאג במקרה של שגיאת פורמט
        print("Sequence: " + " -> ".join([type(m).__name__ for m in messages_to_send]))
        raise e