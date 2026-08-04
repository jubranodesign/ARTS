from langchain_core.messages import SystemMessage
import logging
from langgraph.graph.state import RunnableConfig
from agents.researcher_agent.prompts import RESEARCHER_SYSTEM_PROMPT
from agents.researcher_agent.tools import RESEARCHER_TOOLS
from graph.state import AgentState
from shared.config import setup_node_llm
from shared.paths import extract_target_file_path
from utils.repo_files import read_repo_text_tool_response
from utils.messages import TRIM_TOKENS_RESEARCHER, prepare_chat_history
from utils.state import format_risk_context

logger = logging.getLogger(__name__)

# הצמדת הכלים למופע המשותף

def call_researcher(state: AgentState, config: RunnableConfig):

    llm = setup_node_llm(config, RESEARCHER_TOOLS, node_id="researcher")

    # 1. שליפת נתונים - אנחנו סומכים על ה-main שהזין HumanMessage
    current_summary = state.get("architecture_summary", "No summary available yet.")
    user_task = state.get("user_input", "No task defined.")
    target_file = extract_target_file_path(user_task)
    all_messages = state.get("messages", [])
    risk_context = format_risk_context(state)
    target_file_content = state.get("target_file_code", None)
    
    # אם הוא לא קיים (סיבוב ראשון בלבד!), נקרא אותו עכשיו
    if not target_file_content:
        if target_file:
            repo_path = config["configurable"]["repo_path"]
            target_file_content = read_repo_text_tool_response(repo_path, target_file)
        else:
            target_file_content = "No target file path detected."

    instruction_content = f"""
    {RESEARCHER_SYSTEM_PROMPT}

    {risk_context}

    ### TARGET FILE PATH:
    {target_file}

    ### TARGET FILE SOURCE CODE (READ FIRST):
    ```python
    {target_file_content}
    ```

    ### TARGET TASK:
    {user_task}

    ### CURRENT ARCHITECTURE KNOWLEDGE:
    {current_summary}

    ### EXECUTION GUIDANCE:
    1. TECHNICAL FLOW: Analyze the TARGET FILE SOURCE CODE provided above. Identify its imports and core dependencies. Then, use 'search_dependencies_bm25' to inspect those dependencies, and 'search_golden_tests_semantic' to find reference test patterns.
    2. RISK ANALYSIS FOCUS: Focus your search and analysis on the logic related to the identified risk factors above. Your final data dump must explain how the code implementation contributes to these statistical risks.
    """

    system_msg = SystemMessage(content=instruction_content)

    trimmed_history = prepare_chat_history(
        all_messages, llm, max_tokens=TRIM_TOKENS_RESEARCHER
    )
    messages_to_send = [system_msg] + trimmed_history

    # 6. קריאה למודל
    try:
        response = llm.invoke(messages_to_send)

        state_update = {"messages": [response]}
        if not state.get("target_file_code") and target_file_content:
              state_update["target_file_code"] = target_file_content
              state_update["target_file"] = target_file
        return state_update     
    except Exception as e:
        logger.error("Gemini Error: %s", e)
        # הדפסת סדר ההודעות לדיבאג במקרה של שגיאת פורמט
        logger.debug(
            "Sequence: %s",
            " -> ".join([type(m).__name__ for m in messages_to_send]),
        )
        raise e