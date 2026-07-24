from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph.state import RunnableConfig
from agents.shared.agent_tools import AGENT_TOOLS
from agents.writer_agent.prompts import REPAIR_PROMPT_TEMPLATE, WRITER_PROMPT_TEMPLATE
from agents.writer_agent.tools import WRITER_TOOLS
from graph.state import AgentState
from shared.config import TEST_FRAMEWORK, MOCK_TOOL, setup_node_llm
from shared.logging_rules import SHARED_LOGGING_RULES
from utils.utils import build_agent_messages, count_test_cases_from_list, get_import_path, get_test_path
from utils.failure_analyzer import analyze_test_failure


def call_writer(state: AgentState, config: RunnableConfig):
    repo_path = config["configurable"]["repo_path"]
    # 1. שליפת ההיסטוריה מה-State
    messages = state.get("messages", [])

    # --- בדיקת עצירה (אם הכתיבה/התיקון הצליחו) ---
    if messages and isinstance(messages[-1], ToolMessage):
        last_tool_msg = messages[-1]
        print("last_tool_msg.name ", last_tool_msg.name)

        if last_tool_msg.name == "patch_test_code":
            print("last_tool_msg.content ", last_tool_msg.content)

        # א) טיפול במצב של כתיבת קובץ מלא מושלמת
        if (
            last_tool_msg.name == "write_local_file"
            and "SUCCESS" in last_tool_msg.content.upper()
        ):
            return {
                "messages": [
                    AIMessage(
                        content="Test file has been saved successfully. Task complete."
                    )
                ]
            }

        # ב) טיפול במצב של Patch כירורגי מוצלח - מאפס סטטוס ומחזיר ל-Executor
        if (
            last_tool_msg.name == "patch_test_code"
            and "SUCCESSFULLY" in last_tool_msg.content.upper()
        ):
            print(
                "🔄 Patch applied successfully! Resetting state status and"
                " routing to executor..."
            )
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "I have successfully applied the patch to the test"
                            " file. Routing back to execution."
                        )
                    )
                ],
                "test_run_status": (
                    "pending"  # 👈 מאפס את הסטטוס כדי לא להיתקע בלופ ה-failed
                ),
            }

    # 2. הגדרת ה-LLM
    llm = setup_node_llm(config, AGENT_TOOLS + WRITER_TOOLS)

    # 3. חילוץ נתונים בסיסיים
    target_file = state.get("target_file")
    import_path = get_import_path(target_file)
    test_file_path = get_test_path(target_file)
    root_package = target_file.split("/")[0] if "/" in target_file else ""

    print("root_package: ", root_package)

    # 4. פיצול מסלולים: Repair Mode (כישלון) מול Initial Generation (ריצה ראשונה)
    if state.get("test_run_status") == "failed":
        last_logs = state.get("last_run_logs", "")

        # 🎯 שליפת דיאגנוזה ממוקדת והוראות תיקון מה-Util
        targeted_fix_instruction = analyze_test_failure(
            last_logs, root_package, import_path
        )

        system_prompt = REPAIR_PROMPT_TEMPLATE.format(
                test_file_path=test_file_path,
                last_logs=last_logs,
                targeted_fix_instruction=targeted_fix_instruction,
                root_package=root_package,
                logging_rules=SHARED_LOGGING_RULES,
            )

        system_msg = SystemMessage(content=system_prompt)

        instruction = (
             f"🚨 TEST FAILED.\n"
            f"Do NOT generate explanation text or conversation. You MUST IMMEDIATELY call the `patch_test_code` tool to fix the syntax/logic error in file: {test_file_path}."
         )

    else:
        # 🟢 מסלול כתיבה ראשונית
        plan_text = state.get("test_plan", "")
        tc_count = count_test_cases_from_list(plan_text)
        architecture_summary = state.get(
            "architecture_summary", "No summary available"
        )
        golden_test_summary = state.get(
            "golden_test_summary", "No golden test summary available"
        )

        print("call_writer golden_example: ", golden_test_summary)

        full_prompt = WRITER_PROMPT_TEMPLATE.format(
            repo_path=repo_path,
            target_file=target_file,
            test_file_path=test_file_path,
            plan=plan_text,
            framework=TEST_FRAMEWORK,
            mock_tool=MOCK_TOOL,
            import_path=import_path,
            tc_count=tc_count,
            golden_examples=golden_test_summary,
            architecture_summary=architecture_summary,
            logging_rules=SHARED_LOGGING_RULES,
        )

        system_msg = SystemMessage(
            content=(
                full_prompt
                + f"\n\nCRITICAL: Implement ALL {tc_count} cases identified."
            )
        )

        instruction = (
            f"I see the source code. STOP REASONING NOW.\n"
            f"TASK: Implement the Approved Test Plan based on the ACTUAL source code provided.\n\n"
            f"STRICT RULES (CRITICAL):\n"
            f"1. **SOURCE FIDELITY**: Do not assume logic that doesn't exist. ONLY assert calls visible in the source code.\n"
            f"2. **EXCEPTION REALISM**: Observe how the source handles errors. Match try/except logic exactly.\n"
            f"3. **IMPORT & PATCHING SAFETY**: Follow the MANDATORY BOILERPLATE ORDER defined in the system prompt. Never put the target file `{import_path}` or global pip libraries like `requests` into `sys.modules`.\n"
            f"4. **SMART PATCHING**: For globally imported pip libraries, patch at the root: `mocker.patch('requests.get')`.\n"
            f"5. **EXACT COUNT**: Implement EXACTLY {tc_count} standalone Pytest functions.\n"
            f"6. **EXECUTION**: IMMEDIATELY call `write_local_file` with complete code to: {test_file_path}.\n"
        )

    # 5. בניית ההודעות והפעלת ה-LLM
    input_messages = build_agent_messages(
        state=state,
        system_msg=system_msg,
        target_file=target_file,
        execute_instruction=instruction,
        llm=llm,
    )

    print(f"DEBUG: Writer node - Messages count: {len(input_messages)}")
    print(
        f"DEBUG: Sequence types: {[type(m).__name__ for m in input_messages]}"
    )

    response = llm.invoke(input_messages)

    return {"messages": [response], "test_file_path": test_file_path}