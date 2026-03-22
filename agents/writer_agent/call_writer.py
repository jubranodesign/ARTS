from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph.state import RunnableConfig
from agents.designer_agent.tools import DESIGNER_TOOLS
from agents.writer_agent.prompts import WRITER_PROMPT_TEMPLATE
from agents.writer_agent.tools import WRITER_TOOLS
from graph.state import AgentState
from shared.config import REPO_PATH, TEST_FRAMEWORK, MOCK_TOOL, setup_node_llm
from utils.utils import build_agent_messages, count_test_cases_from_list, get_import_path, get_test_path

def call_writer(state: AgentState, config: RunnableConfig):
    # 1. שליפת ההיסטוריה מה-State
    messages = state.get("messages", [])
    
    # --- בדיקת עצירה (אם הכתיבה הצליחה) ---
    if messages and isinstance(messages[-1], ToolMessage):
        if messages[-1].name == "write_local_file" and "SUCCESS" in messages[-1].content.upper():
            return {"messages": [AIMessage(content="Test file has been saved successfully. Task complete.")]}

    # 2. הגדרת ה-LLM (לפי ההמלצה: Qwen-2.5-32b לביצוע מדויק של Mocks)
    llm = setup_node_llm(config, DESIGNER_TOOLS + WRITER_TOOLS) 
    
    # 3. חילוץ נתונים
    target_file = state.get("target_file")
    import_path = get_import_path(target_file)
    test_file_path = get_test_path(target_file)
    plan_text = state.get("test_plan", "")
    tc_count = count_test_cases_from_list(plan_text)
    
    # 4. בניית ה-System Message (ה-Prompt המלא)
    full_prompt = WRITER_PROMPT_TEMPLATE.format(
        repo_path=REPO_PATH,
        target_file=target_file,
        test_file_path=test_file_path,
        plan=plan_text,
        framework=TEST_FRAMEWORK,
        mock_tool=MOCK_TOOL,
        import_path=import_path,
        tc_count=tc_count
    )
    system_msg = SystemMessage(content=full_prompt + f"\n\nCRITICAL: Implement ALL {tc_count} cases identified.")

    # 5. הגדרת ה-Instruction לביצוע (שלב ב')
    # אנחנו בודקים אם מדובר בתיקון שגיאות או בכתיבה חדשה
    if state.get("test_run_status") == "failed":
        instruction = (
            f"🚨 TEST FAILED. You must fix the code in `{test_file_path}`.\n"
            f"ERROR LOGS:\n{state.get('last_run_logs')}\n"
            f"Refer to the source code and the original Test Plan. Fix the Mocks or Logic."
        )
    else:
        instruction = (
            f"I see the source code. STOP REASONING NOW.\n"
            f"TASK: Implement the Approved Test Plan EXACTLY as written above.\n\n"
            f"STRICT RULES (CRITICAL):\n"
            f"1. **EXACT COUNT**: Implement EXACTLY {tc_count} standalone Pytest functions.\n"
            f"2. **PATCH PATH**: Use: `mocker.patch('{import_path}.requests.get')`.\n"
            f"3. **IMPORTS**: Include 'import pytest', 'import requests', 'import json'.\n"
            f"4. **EXECUTION**: IMMEDIATELY call `write_local_file` to: {test_file_path}.\n"
            f"DO NOT explain. Just generate the code."
        )

    # 6. שימוש ב-Helper האחיד (מטפל ב-Trim ובמניעת לופים)
    input_messages = build_agent_messages(
        state=state,
        system_msg=system_msg,
        target_file=target_file,
        execute_instruction=instruction,
        llm=llm
    )

    # דיבאג לפורמט
    print(f"DEBUG: Writer node - Messages count: {len(input_messages)}")
    print(f"DEBUG: Sequence types: {[type(m).__name__ for m in input_messages]}")

    # 7. הפעלה
    response = llm.invoke(input_messages)
    
    return {
        "messages": [response],
        "test_file_path": test_file_path
    }