from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage
from agents.designer_agent.prompts import REVIEWER_PROMPT_TEMPLATE
from agents.designer_agent.tools import DESIGNER_TOOLS
from shared.config import setup_node_llm
from utils.utils import get_import_path

def call_reviewer(state, config):
    llm = setup_node_llm(config, DESIGNER_TOOLS)
    
    # 1. שליפת נתונים מה-State
    all_messages = state.get("messages", [])
    target_file = state.get("target_file")
    import_path = get_import_path(target_file)
    
    # לוקחים את ה-Plan הכי מעודכן שנשמר ב-State (הכי בטוח)
    test_plan = state.get("test_plan", "No draft found in state")

    # 2. הכנת הפרומפט (הזרקת המשתנים ל-System)
    system_content = REVIEWER_PROMPT_TEMPLATE.format(
        target_file=target_file,
        import_path=import_path
    )
    system_message = SystemMessage(content=system_content)
    
    # 3. בקשת הביקורת (Human Message)
    human_request = HumanMessage(content=f"Please review the following test plan draft:\n\n{test_plan}")

    # 4. הרצה עם ההיסטוריה המלאה
    try:
        # אנחנו שולחים: [היסטוריה] + [הנחיות מערכת] + [בקשה נוכחית]
        # זה מבטיח שהוא רואה את ה-ToolMessage עם הקוד מה-Designer
        response = llm.invoke([system_message, human_request] + all_messages)
        
        return {"messages": [response]}
    except Exception as e:
        print(f"❌ Reviewer Error: {e}")
        return {"messages": [AIMessage(content=f"Reviewer failed: {str(e)}")]}