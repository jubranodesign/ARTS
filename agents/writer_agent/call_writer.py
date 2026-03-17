from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph.state import RunnableConfig
from agents.designer_agent.tools import DESIGNER_TOOLS
from agents.writer_agent.prompts import WRITER_PROMPT_TEMPLATE
from agents.writer_agent.tools import WRITER_TOOLS
from graph.state import AgentState
from shared.config import REPO_PATH, TEST_FRAMEWORK, MOCK_TOOL, setup_node_llm
from utils.utils import count_test_cases_from_list, extract_python_path, get_test_path

def call_writer(state: AgentState, config: RunnableConfig):
    # שליפת ההיסטוריה מה-State
    messages = state.get("messages", [])
    
    # ---------------------------------------------------------
    # 1. בדיקת עצירה (הבדיקה ששאלת עליה):
    # אם ההודעה האחרונה היא ToolMessage והיא מדווחת על הצלחה בכתיבה - 
    # אנחנו מחזירים הודעת סיום ולא מפעילים את ה-LLM בכלל.
    # ---------------------------------------------------------
    if messages and isinstance(messages[-1], ToolMessage):
        if messages[-1].name == "write_local_file" and "SUCCESS" in messages[-1].content.upper():
            return {"messages": [AIMessage(content="Test file has been saved successfully. Task complete.")]}

    # 2. הגדרת ה-LLM עם הכלים (רק אם לא עצרנו בשלב 1)
    llm = setup_node_llm(config, DESIGNER_TOOLS + WRITER_TOOLS) 
    
    # 3. חילוץ נתונים בסיסיים
    user_input = state.get("user_input", "")
    target_file = extract_python_path(user_input)

    # 4. הכנת נתיבי עבודה (ה-Import והנתיב של הטסט)
    import_path = target_file.replace('/', '.').replace('.py', '')
    test_file_path = get_test_path(target_file)
    
    # חישוב מספר מקרי הבדיקה בתוכנית
    plan_text = state.get("test_plan", "")
    tc_count = count_test_cases_from_list(plan_text)
    print(f"tc_count: {tc_count}")

    # 5. בדיקה האם כבר קראנו את הקובץ (כדי לדעת אם לבקש READ או WRITE)
    already_read = any(
        isinstance(m, ToolMessage) and m.name == "read_local_file" 
        for m in messages
    )

    if not already_read:
        # --- שלב א': בקשת קריאה (פעם ראשונה) ---
        # ... (הקוד הקיים שלך לבניית ה-system_content ו-input_messages)
    
        full_prompt = WRITER_PROMPT_TEMPLATE.format(
            repo_path=REPO_PATH,
            target_file=target_file,
            test_file_path=test_file_path,
            plan=state.get("test_plan", ""),
            framework=TEST_FRAMEWORK,
            mock_tool=MOCK_TOOL,
            import_path=import_path,
            tc_count=tc_count
        )
        
        system_content = full_prompt + f"\n\nCRITICAL: I identified {tc_count} test cases in the plan. You will be required to implement ALL {tc_count} cases."

        input_messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=f"Please start by reading the source code of: {target_file}")
        ]
    else:
        # --- שלב ב': כתיבת קוד או תיקון שגיאות ---
        # בדיקה אם אנחנו בסבב תיקון (Self-Healing)

        if state.get("test_run_status") == "failed":
            instruction = (
        f"🚨 STRICT ACTION REQUIRED: The previous test execution FAILED.\n"
        f"ERROR LOGS:\n{state.get('last_run_logs')}\n"
        f"FILE TO FIX: {test_file_path}\n\n"
        f"STEP 1: Use `read_local_file` to read the current content of {test_file_path}.\n"
        f"STEP 2: Identify EXACTLY which test functions failed based on the logs.\n"
        f"STEP 3: Instead of rewriting the entire file, use the `patch_test_code` tool.\n"
        f"STEP 4: For each failed test, provide a SEARCH block (the old, broken code) "
        f"and a REPLACE block (the fixed code with correct Mocks/Side-effects).\n"
        f"⚠️ CRITICAL: Ensure the SEARCH block matches the file content EXACTLY, including spaces."
    )
    #        instruction = (
    #     f"STRICT ACTION REQUIRED: The previous test execution FAILED.\n"
    #     f"ERROR LOGS:\n{state.get('last_run_logs')}\n"
    #     f"FILE TO FIX: {test_file_path}\n\n" # הנתיב היחסי
    #     f"STEP 1: Use `read_local_file` to read the current content of {test_file_path}.\n"
    #     f"STEP 2: Analyze why it failed based on the logs.\n"
    #     f"STEP 3: Fix the code and implement ALL {tc_count} cases correctly.\n"
    #     f"STEP 4: Call `write_local_file` with the corrected code.\n"
    #     f"DO NOT guess the code. Read it first."
    # )
        else:
            # הוראת כתיבה רגילה (פעם ראשונה)
            # instruction = (
            #     f"I see the source code. STOP REASONING NOW.\n"
            #     f"TASK: Implement EXACTLY {tc_count} standalone Pytest functions.\n"
            #     f"STRICT RULES:\n"
            #     f"1. You MUST use the `mocker` fixture to patch `requests.get` in EVERY test.\n"
            #     f"2. You MUST include 'import pytest', 'import requests', and 'import json'.\n"
            #     f"3. IMMEDIATELY call `write_local_file` with the full code to: {test_file_path}."
            # )
        # instruction = (
        #     f"I see the source code. DO NOT PROVIDE REASONING. "
        #     f"Directly generate the Pytest code for the {tc_count} cases "
        #     f"and call the `write_local_file` tool IMMEDIATELY. "
        #     f"If you spend tokens on explanation, you will fail the task."
        # )

        # instruction = (
        #     f"I see the source code. Now, implement the Pytest code. "
        #     f"REMINDER: The plan has {tc_count} test cases. "
        #     f"You MUST implement EXACTLY {tc_count} test functions, one for each TC ID. "
        #     f"Save the complete code to {test_file_path} using write_local_file."
        # )

          instruction = (
            f"I see the source code. STOP REASONING NOW.\n"
            f"TASK: Implement EXACTLY {tc_count} standalone Pytest functions.\n"
            f"STRICT RULES:\n"
            f"1. You MUST use the `mocker` fixture to patch `requests.get` in EVERY test. NO real network calls.\n"
            f"2. You MUST include 'import pytest', 'import requests', and 'import json' if needed.\n"
            f"3. You MUST implement one function per TC ID identified in the plan.\n"
            f"4. IMMEDIATELY call `write_local_file` with the full code to: {test_file_path}.\n"
            f"DO NOT explain. Just code and save."
        )

        # --- שלב ב': בקשת כתיבה ---
        # המודל כבר ראה את תוכן הקובץ ב-messages הקודמים
        input_messages = messages + [
            HumanMessage(content=instruction)
        ]

    # 6. הפעלה סופית של המודל
    response = llm.invoke(input_messages)
    
    # החזרת ה-response יחד עם שמירת הנתיבים ב-State
    return {
        "messages": [response],
        "target_file": target_file,       # קובץ המקור (למשל: src/logic.py)
        "test_file_path": test_file_path  # קובץ הטסט (למשל: tests/test_logic.py)
    }