import logging

from langchain_core.messages import SystemMessage
from langgraph.graph.state import RunnableConfig

from shared.repo_language import get_designer_prompt_template
from agents.shared.agent_tools import AGENT_TOOLS
from graph.state import AgentState
from shared.config import setup_node_llm
from shared.logging_rules import SHARED_LOGGING_RULES
from utils.utils import build_agent_messages

logger = logging.getLogger(__name__)


def call_designer(state: AgentState, config: RunnableConfig):
    # 1. הגדרת ה-LLM (לפי ההמלצה: Qwen-2.5-32b או Gemini)
    llm = setup_node_llm(config, AGENT_TOOLS)

    # 2. שליפת נתונים בסיסיים מה-State
    architecture_summary = state.get("architecture_summary", "No summary available")
    golden_test_summary = state.get("golden_test_summary", "No golden test summary available")
    user_input = state.get("user_input", "")
    target_file = state.get("target_file") 

    # 3. בניית ה-System Message (ה-Prompt המועשר)
    enriched_prompt_content = get_designer_prompt_template().format(
        architecture_summary=architecture_summary,
        golden_examples=golden_test_summary,
        user_input=user_input,
        logging_rules=SHARED_LOGGING_RULES,
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

    logger.debug(
        "Designer node messages count=%s sequence_types=%s",
        len(messages_to_send),
        [type(m).__name__ for m in messages_to_send],
    )

    # 5. קריאה למודל
    try:
        response = llm.invoke(messages_to_send)
        return {"messages": [response]}
    except Exception as e:
        logger.error("Designer LLM Error: %s", e)
        logger.debug(
            "Final sequence: %s",
            " -> ".join([type(m).__name__ for m in messages_to_send]),
        )
        raise e
