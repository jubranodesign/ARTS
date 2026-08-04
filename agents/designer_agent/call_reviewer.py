import logging

from langchain_core.messages import AIMessage, SystemMessage

from shared.repo_language import get_reviewer_prompt_template
from agents.shared.agent_tools import AGENT_TOOLS
from shared.config import setup_node_llm
from shared.logging_rules import SHARED_LOGGING_RULES
from utils.utils import build_agent_messages

logger = logging.getLogger(__name__)


def call_reviewer(state, config):
    # 1. הגדרת המודל (לפי ההמלצה: Llama-3.3-70b-versatile לביקורתיות מקסימלית)
    llm = setup_node_llm(config, AGENT_TOOLS, node_id="reviewer")
    
    # 2. שליפת נתונים מה-State
    target_file = state.get("target_file")
    test_plan = state.get("test_plan", "No draft found in state")
    architecture_summary = state.get("architecture_summary", "No summary available")
    golden_test_summary = state.get("golden_test_summary", "No golden test summary available")

    # 3. הכנת הפרומפט (הזרקת המשתנים ל-System)
    system_content = get_reviewer_prompt_template().format(
        architecture_summary=architecture_summary,
        golden_examples=golden_test_summary,
        logging_rules=SHARED_LOGGING_RULES
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

    logger.debug(
        "Reviewer node messages count=%s sequence_types=%s",
        len(messages_to_send),
        [type(m).__name__ for m in messages_to_send],
    )

    # 6. הרצה
    try:
        response = llm.invoke(messages_to_send)
        return {"messages": [response]}
    except Exception as e:
        logger.error("Reviewer Error: %s", e)
        logger.debug(
            "Final sequence: %s",
            " -> ".join([type(m).__name__ for m in messages_to_send]),
        )
        return {"messages": [AIMessage(content=f"Reviewer failed: {str(e)}")]}
