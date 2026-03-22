from langchain_core.messages import AIMessage, SystemMessage
from agents.designer_agent.prompts import REVIEWER_PROMPT_TEMPLATE
from agents.designer_agent.tools import DESIGNER_TOOLS
from shared.config import setup_node_llm
from utils.utils import build_agent_messages, get_import_path

def call_reviewer(state, config):
    # 1. הגדרת המודל (לפי ההמלצה: Llama-3.3-70b-versatile לביקורתיות מקסימלית)
    llm = setup_node_llm(config, DESIGNER_TOOLS)
    
    # 2. שליפת נתונים מה-State
    target_file = state.get("target_file")
    import_path = get_import_path(target_file)
    test_plan = state.get("test_plan", "No draft found in state")

    # 3. הכנת הפרומפט (הזרקת המשתנים ל-System)
    system_content = REVIEWER_PROMPT_TEMPLATE.format(
        target_file=target_file,
        import_path=import_path
    )
    system_message = SystemMessage(content=system_content)
    
    # 4. שימוש ב-Helper האחיד שלנו
    # הוראת הביצוע כוללת את ה-Plan שצריך לבקר
    execute_instr = (
    f"I see the source code. Now, review the plan below.\n\n"
    f"DRAFT PLAN:\n{test_plan}\n\n"
    f"IMPORTANT: You MUST start with '## Review Notes' and then provide the '## Final Test Plan'. "
    f"If a test case isn't supported by the code, DELETE it."
)

    messages_to_send = build_agent_messages(
        state=state,
        system_msg=system_message,
        target_file=target_file,
        execute_instruction=execute_instr,
        llm=llm
    )

    # 5. דיבאג (העיניים שלנו על הפורמט)
    print(f"DEBUG: Reviewer node - Messages count: {len(messages_to_send)}")
    print(f"DEBUG: Sequence types: {[type(m).__name__ for m in messages_to_send]}")

    # 6. הרצה
    try:
        response = llm.invoke(messages_to_send)
        return {"messages": [response]}
    except Exception as e:
        print(f"❌ Reviewer Error: {e}")
        # הדפסת הרצף במקרה של שגיאה (מאוד עוזר ב-Gemini/Llama)
        print("Final Sequence: " + " -> ".join([type(m).__name__ for m in messages_to_send]))
        return {"messages": [AIMessage(content=f"Reviewer failed: {str(e)}")]}