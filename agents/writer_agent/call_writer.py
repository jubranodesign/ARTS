from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph.state import RunnableConfig
from agents.designer_agent.tools import DESIGNER_TOOLS
from agents.writer_agent.prompts import WRITER_PROMPT_TEMPLATE
from agents.writer_agent.tools import WRITER_TOOLS
from graph.state import AgentState
from shared.config import REPO_PATH, TEST_FRAMEWORK, MOCK_TOOL, setup_node_llm
from utils.utils import count_test_cases_from_list, get_import_path, get_test_path


def call_writer(state: AgentState, config: RunnableConfig):
    # 1. שליפת ההיסטוריה מה-State
    messages = state.get("messages", [])
    
    # --- בדיקת עצירה (אם הכתיבה הצליחה) ---
    if messages and isinstance(messages[-1], ToolMessage):
        if messages[-1].name == "write_local_file" and "SUCCESS" in messages[-1].content.upper():
            return {"messages": [AIMessage(content="Test file has been saved successfully. Task complete.")]}

    # 2. הגדרת ה-LLM
    llm = setup_node_llm(config, DESIGNER_TOOLS + WRITER_TOOLS) 
    
    # 3. חילוץ נתונים
    target_file = state.get("target_file")
    import_path = get_import_path(target_file)
    test_file_path = get_test_path(target_file)
    
    # שליפת ה-Plan והספירה
    plan_text = state.get("test_plan", "")
    tc_count = count_test_cases_from_list(plan_text)
    
    # 4. בדיקה האם כבר קראנו את הקובץ
    already_read = any(
        isinstance(m, ToolMessage) and m.name == "read_local_file"
        for m in messages
    )

    print("call_writer already_read ", already_read)

    if not already_read:
        # --- שלב א': בקשת קריאה (פעם ראשונה) ---
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
        
        system_content = full_prompt + f"\n\nCRITICAL: Implement ALL {tc_count} cases identified."

        input_messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=f"Please start by reading the source code of: {target_file}")
        ]
    else:
        # --- שלב ב': כתיבת קוד (עם ה-Instruction המשופר) ---
        if state.get("test_run_status") == "failed":
            instruction = (
                f"🚨 TEST FAILED. You must fix the code in `{test_file_path}`.\n"
                f"ERROR LOGS:\n{state.get('last_run_logs')}\n"
                f"Refer to the source code and the original Test Plan."
            )
        else:
            # ה-Instruction המנצח שמשלב את הדיוק של ה-Patch Path
            instruction = (
                f"I see the source code. STOP REASONING NOW.\n"
                f"TASK: Implement the Approved Test Plan EXACTLY as written above.\n\n"
                f"STRICT RULES (CRITICAL):\n"
                f"1. **EXACT COUNT**: Implement EXACTLY {tc_count} standalone Pytest functions. One for each TC ID.\n"
                f"2. **PATCH PATH**: Use the specific path: `mocker.patch('{import_path}.requests.get')` in EVERY test. NO exceptions.\n"
                f"3. **IMPORTS**: You MUST include 'import pytest', 'import requests', and 'import json' at the top.\n"
                f"4. **NO NETWORK**: Use the `mocker` fixture for everything. NO real network calls.\n"
                f"5. **EXECUTION**: IMMEDIATELY call `write_local_file` with the full code to: {test_file_path}.\n\n"
                f"DO NOT explain your logic. Just generate the code and save it."
            )

        # שרשור ההודעות ששומר על ה-ToolMessage בזיכרון של המודל
        input_messages = messages + [HumanMessage(content=instruction)]

    # 5. הפעלה
    response = llm.invoke(input_messages)
    
    return {
        "messages": [response],
        "test_file_path": test_file_path
    }