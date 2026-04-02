from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph.state import RunnableConfig
from agents.designer_agent.tools import DESIGNER_TOOLS
from agents.writer_agent.prompts import WRITER_PROMPT_TEMPLATE
from agents.writer_agent.tools import WRITER_TOOLS
from graph.state import AgentState
from shared.config import REPO_PATH, TEST_FRAMEWORK, MOCK_TOOL, setup_node_llm
from utils.utils import build_agent_messages, count_test_cases_from_list, get_import_path, get_test_path, parse_architecture_summary

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
    summary_text = state.get("architecture_summary", "")
    parsed_summary = parse_architecture_summary(summary_text)
    golden_example = parsed_summary.get("golden_example", "No reference pattern found.")
    print("call_writer golden_example: ", golden_example)
    
    # 4. בניית ה-System Message (ה-Prompt המלא)
    full_prompt = WRITER_PROMPT_TEMPLATE.format(
        repo_path=REPO_PATH,
        target_file=target_file,
        test_file_path=test_file_path,
        plan=plan_text,
        framework=TEST_FRAMEWORK,
        mock_tool=MOCK_TOOL,
        import_path=import_path,
        tc_count=tc_count,
        golden_example=golden_example
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
        # instruction = (
        #     f"I see the source code. STOP REASONING NOW.\n"
        #     f"TASK: Implement the Approved Test Plan EXACTLY as written above.\n\n"
        #     f"STRICT RULES (CRITICAL):\n"
        #     f"1. **EXACT COUNT**: Implement EXACTLY {tc_count} standalone Pytest functions.\n"
        #     f"2. **PATCH PATH**: Use: `mocker.patch('{import_path}.requests.get')`.\n"
        #     f"3. **IMPORTS**: Include 'import pytest', 'import requests', 'import json'.\n"
        #     f"4. **EXECUTION**: IMMEDIATELY call `write_local_file` to: {test_file_path}.\n"
        #     f"DO NOT explain. Just generate the code."
        # )
#         instruction = (
#     f"I see the source code. STOP REASONING NOW.\n"
#     f"TASK: Implement the Approved Test Plan EXACTLY as written above.\n\n"
#     f"STRICT RULES (CRITICAL):\n"
#     f"1. **REFERENCE USE**: Review the provided Chunks from past successful tests and mimic their mocking patterns.\n"
#     f"2. **IMPORT SAFETY**: If you detect 'sqlmodel' or DB imports in the source, use `sys.modules` patching BEFORE the main import to prevent ImportError.\n"
#     f"3. **EXACT COUNT**: Implement EXACTLY {tc_count} standalone Pytest functions.\n"
#     f"4. **PATCH PATH**: Use: `mocker.patch('{import_path}.requests.get')`.\n"
#     f"5. **EXECUTION**: IMMEDIATELY call `write_local_file` to: {test_file_path}.\n"
#     f"DO NOT explain. Just generate the code."
# )
    #   instruction = (
    #         f"I see the source code. STOP REASONING NOW.\n"
    #         f"TASK: Implement the Approved Test Plan EXACTLY as written above.\n\n"
    #         f"STRICT RULES (CRITICAL):\n"
    #         f"1. **REFERENCE USE**: Review the 'GOLDEN EXAMPLE' and mimic its mocking patterns.\n"
    #         f"2. **IMPORT SAFETY**: You MUST use `sys.modules` patching for ALL internal modules (like scraper_api, common.db) BEFORE the main import to prevent ModuleNotFoundError.\n"
    #         f"3. **EXACT COUNT**: Implement EXACTLY {tc_count} standalone Pytest functions.\n"
    #         f"4. **SMART PATCHING**: ONLY patch what is imported in the source. If `requests` is NOT in source imports, patch the local function instead (e.g., `mocker.patch('{import_path}.fetch_studies')`).\n"
    #         f"5. **EXECUTION**: IMMEDIATELY call `write_local_file` with complete code to: {test_file_path}.\n"
    #         f"DO NOT explain. Just generate the code."
    #     )
     instruction = (
    f"I see the source code. STOP REASONING NOW.\n"
    f"TASK: Implement the Approved Test Plan based on the ACTUAL source code provided.\n\n"
    f"STRICT RULES (CRITICAL):\n"
    f"1. **SOURCE FIDELITY**: Do not assume logic that doesn't exist. ONLY assert calls (like commit, save, fetch) that are visible in the source code. If the code doesn't call a method (e.g., rollback), do not test for it.\n"
    f"2. **EXCEPTION REALISM**: Observe how the source handles errors. If the source uses try/except to catch an error, the test should NOT use `pytest.raises`. If the source let an error propagate (like fetch_studies), the test MUST handle it accordingly.\n"
    f"3. **IMPORT SAFETY**: You MUST use `sys.modules` patching for `scraper_api`, `common.db`, and `psycopg2` BEFORE the main import.\n"
    f"4. **SMART PATCHING**: Patch what is imported. Use `mocker.patch('{import_path}.fetch_studies')` for API calls.\n"
    f"5. **EXACT COUNT**: Implement EXACTLY {tc_count} standalone functions.\n"
    f"6. **EXECUTION**: IMMEDIATELY call `write_local_file` with complete code to: {test_file_path}.\n"
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