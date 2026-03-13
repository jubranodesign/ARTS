from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage
from agents.designer_agent.prompts import REVIEWER_PROMPT_TEMPLATE
from agents.designer_agent.tools import DESIGNER_TOOLS
from shared.config import setup_node_llm
from utils.utils import get_clean_text

def call_reviewer(state, config):
    llm = setup_node_llm(config, DESIGNER_TOOLS)
    all_messages = state["messages"]
    
    # 1. שליפת הטיוטה
    # שימוש ב-get_clean_text שכתבת קודם כדי לוודא שאין רשימות מוזרות
    ai_msgs = [get_clean_text(m.content) for m in all_messages if isinstance(m, AIMessage) and m.content]
    last_draft = ai_msgs[-1] if ai_msgs else "No draft found"

    # 2. בניית הפרומפט
    # שים לב: אנחנו לא מזריקים את ה-draft לתוך ה-SystemMessage, אלא נפריד ביניהם
    system_message = SystemMessage(content=REVIEWER_PROMPT_TEMPLATE)
    human_request = HumanMessage(content=f"Please review the following test plan draft:\n\n{last_draft}")

    # 3. הפתרון לשגיאה: שולחים גם System וגם Human
    try:
        # כאן Gemini יקבל את ה-contents שהוא מחפש
        response = llm.invoke([system_message, human_request])
        return {"messages": [response]}
    except Exception as e:
        # הגנה למקרה של תקלה ב-API
        print(f"❌ Gemini Error: {e}")
        return {"messages": [AIMessage(content=f"Reviewer failed: {str(e)}")]}