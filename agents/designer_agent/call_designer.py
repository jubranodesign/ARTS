from langchain_core.messages import SystemMessage
from langgraph.graph.state import RunnableConfig
from agents.designer_agent.prompts import DESIGNER_PROMPT_TEMPLATE
from agents.shared.agent_tools import AGENT_TOOLS
from graph.state import AgentState
from shared.config import setup_node_llm
from utils.utils import build_agent_messages


def call_designer(state: AgentState, config: RunnableConfig):
    # 1. הגדרת ה-LLM (לפי ההמלצה: Qwen-2.5-32b או Gemini)
    llm = setup_node_llm(config, AGENT_TOOLS)

    # 2. שליפת נתונים בסיסיים מה-State
    architecture_summary = state.get("architecture_summary", "No summary available")
    user_input = state.get("user_input", "")
    target_file = state.get("target_file") # וודא שזה קיים ב-State

    # 3. בניית ה-System Message (ה-Prompt המועשר)
    enriched_prompt_content = DESIGNER_PROMPT_TEMPLATE.format(
        architecture_summary=architecture_summary,
        user_input=user_input
    )
    system_msg = SystemMessage(content=enriched_prompt_content)

    # 4. שימוש ב-Helper הגנרי מה-Utils (זה מחליף את שלבים 3-5 בקוד הישן שלך)
    # ה-Helper מטפל ב-already_read, ב-Trim ובניקוי הודעות מערכת ישנות.
    messages_to_send = build_agent_messages(
        state=state,
        system_msg=system_msg,
        target_file=target_file,
        execute_instruction=f"I see the source code. Now, Design tests for the following request: {user_input}",
        llm=llm
    )

    # דיבאג (חשוב כדי לראות שאין כפילות של System)
    print(f"DEBUG: Designer node - Messages count: {len(messages_to_send)}")
    print(f"DEBUG: Sequence types: {[type(m).__name__ for m in messages_to_send]}")

    # 5. קריאה למודל
    try:
        response = llm.invoke(messages_to_send)
        return {"messages": [response]}
    except Exception as e:
        print(f"❌ Designer LLM Error: {e}")
        # הדפסת הרצף במקרה של שגיאה (עוזר מאוד עם Llama/Gemini)
        print("Final Sequence: " + " -> ".join([type(m).__name__ for m in messages_to_send]))
        raise e