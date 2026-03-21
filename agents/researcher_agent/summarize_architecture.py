from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph.state import RunnableConfig
from agents.researcher_agent.models import ArchitectureSnapshot
from agents.researcher_agent.prompts import ARCHITECT_SUMMARY_PROMPT
from graph.state import AgentState
from shared.config import setup_node_llm
from utils.utils import extract_python_path, get_clean_text
from langchain_core.messages import RemoveMessage
from langchain_core.messages import RemoveMessage, SystemMessage, HumanMessage

def summarize_architecture(state: AgentState, config: RunnableConfig):
    """
    צומת המסכם: לוקח את התובנה האחרונה, מזקק אותה לסיכום בהקשר למשימה, ומנקה היסטוריה.
    """
    llm = setup_node_llm(config)

    # 1. שליפת הודעות, סיכום קיים והמשימה המקורית
    all_messages = state.get("messages", [])
    current_summary = state.get("architecture_summary", "No summary yet.")
    user_task = state.get("user_input", "No specific task defined.") # הוספת ה-user_input
    target_file = extract_python_path(user_task)

    # 2. מציאת הודעת ה-AI האחרונה
    ai_messages = [m for m in all_messages if m.type == "ai" and m.content]
    
    if not ai_messages:
        print("⚠️ No AI insights found in history to summarize.")
        return {} 

    # 3. ניקוי הממצא האחרון
    last_ai_msg = ai_messages[-1]
    clean_research = get_clean_text(last_ai_msg.content)
    

    summary_task = f"Document the architecture and logic of {target_file} based on the research data."
    # 4. הכנת הפרומפט - הוספנו את user_task כדי שהסיכום יהיה ממוקד מטרה
    # הנחה: ARCHITECT_SUMMARY_PROMPT תומך בפרמטר user_task
    final_prompt = ARCHITECT_SUMMARY_PROMPT.format(
        current_summary=current_summary,
        research_data=clean_research,
        user_task=summary_task # הזרקת המשימה למסכם
    )

    input_messages = [
        SystemMessage(content="You are a system architect extraction tool. Focus on details relevant to the user task."),
        HumanMessage(content=final_prompt)
    ]

    # 5. קריאה למודל עם Structured Output
    structured_llm = llm.with_structured_output(ArchitectureSnapshot)
    
    try:
        result = structured_llm.invoke(input_messages)
    except Exception as e:
        print(f"❌ Error during structured invoke: {e}")
        return {}
    
    if not result or not result.summary:
        print("❌ Summarizer failed.")
        return {}

    print(f"✅ Architecture snapshot updated. Confidence: {result.confidence_score}")

    # 6. ניקוי השולחן
    delete_messages = [RemoveMessage(id=m.id) for m in all_messages]

    return {
        "architecture_summary": result.summary,
        "target_file": target_file,
        "messages": delete_messages 
    }