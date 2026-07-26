from dataclasses import dataclass
from typing import Optional

import logging

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph.state import RunnableConfig

from agents.writer_agent.prompts import REPAIR_PROMPT_TEMPLATE, WRITER_PROMPT_TEMPLATE
from graph.state import AgentState
from shared.constants import MOCK_TOOL, TEST_FRAMEWORK
from shared.logging_rules import SHARED_LOGGING_RULES
from utils.failure_analyzer import analyze_test_failure
from utils.log_format import log_tail
from utils.utils import count_test_cases_from_list, get_import_path, get_test_path

logger = logging.getLogger(__name__)


@dataclass
class WriterContext:
    repo_path: str
    target_file: str
    import_path: str
    test_file_path: str
    root_package: str


def handle_post_tool_success(state: AgentState) -> Optional[dict]:
    """Early return after successful write_local_file or patch_test_code."""
    messages = state.get("messages", [])
    if not messages or not isinstance(messages[-1], ToolMessage):
        return None

    last_tool_msg = messages[-1]
    logger.debug("last_tool_msg.name %s", last_tool_msg.name)

    if last_tool_msg.name == "patch_test_code":
        logger.debug("last_tool_msg.content %s", last_tool_msg.content)

    if (
        last_tool_msg.name == "write_local_file"
        and "SUCCESS" in last_tool_msg.content.upper()
    ):
        return {
            "messages": [
                AIMessage(content="Test file has been saved successfully. Task complete.")
            ]
        }

    if (
        last_tool_msg.name == "patch_test_code"
        and "SUCCESSFULLY" in last_tool_msg.content.upper()
    ):
        logger.info("Patch applied successfully; resetting state status and routing to executor")
        return {
            "messages": [
                AIMessage(
                    content=(
                        "I have successfully applied the patch to the test"
                        " file. Routing back to execution."
                    )
                )
            ],
            "test_run_status": "pending",
        }

    return None


def build_writer_context(state: AgentState, config: RunnableConfig) -> WriterContext:
    target_file = state.get("target_file")
    import_path = get_import_path(target_file)
    test_file_path = get_test_path(target_file)
    root_package = target_file.split("/")[0] if "/" in target_file else ""
    logger.debug("root_package: %s", root_package)

    return WriterContext(
        repo_path=config["configurable"]["repo_path"],
        target_file=target_file,
        import_path=import_path,
        test_file_path=test_file_path,
        root_package=root_package,
    )


def build_repair_messages(ctx: WriterContext, state: AgentState) -> tuple[SystemMessage, str]:
    last_logs = state.get("last_run_logs", "")
    logger.debug(
        "build_repair_messages test_file_path=%s root_package=%r import_path=%r logs_len=%s",
        ctx.test_file_path,
        ctx.root_package,
        ctx.import_path,
        len(last_logs or ""),
    )
    targeted_fix_instruction = analyze_test_failure(
        last_logs, ctx.root_package, ctx.import_path
    )
    logger.debug(
        "build_repair_messages targeted_fix_instruction preview: %s",
        log_tail(targeted_fix_instruction, max_chars=500, max_lines=15),
    )

    system_prompt = REPAIR_PROMPT_TEMPLATE.format(
        test_file_path=ctx.test_file_path,
        last_logs=last_logs,
        targeted_fix_instruction=targeted_fix_instruction,
        root_package=ctx.root_package,
        logging_rules=SHARED_LOGGING_RULES,
    )
    system_msg = SystemMessage(content=system_prompt)
    instruction = (
        f"🚨 TEST FAILED.\n"
        f"Do NOT generate explanation text or conversation. You MUST IMMEDIATELY call the "
        f"`patch_test_code` tool to fix the syntax/logic error in file: {ctx.test_file_path}."
    )
    logger.debug(
        "build_repair_messages system_prompt_len=%s instruction_len=%s",
        len(system_prompt),
        len(instruction),
    )
    return system_msg, instruction


def build_generate_messages(ctx: WriterContext, state: AgentState) -> tuple[SystemMessage, str]:
    plan_text = state.get("test_plan", "")
    tc_count = count_test_cases_from_list(plan_text)
    architecture_summary = state.get("architecture_summary", "No summary available")
    golden_test_summary = state.get("golden_test_summary", "No golden test summary available")

    logger.debug(
        "build_generate_messages target_file=%s test_file_path=%s tc_count=%s "
        "plan_len=%s golden_len=%s arch_len=%s",
        ctx.target_file,
        ctx.test_file_path,
        tc_count,
        len(plan_text or ""),
        len(golden_test_summary or ""),
        len(architecture_summary or ""),
    )
    logger.debug("build_generate_messages golden_test_summary preview: %s", log_tail(golden_test_summary, max_chars=400, max_lines=10))

    full_prompt = WRITER_PROMPT_TEMPLATE.format(
        repo_path=ctx.repo_path,
        target_file=ctx.target_file,
        test_file_path=ctx.test_file_path,
        plan=plan_text,
        framework=TEST_FRAMEWORK,
        mock_tool=MOCK_TOOL,
        import_path=ctx.import_path,
        tc_count=tc_count,
        golden_examples=golden_test_summary,
        architecture_summary=architecture_summary,
        logging_rules=SHARED_LOGGING_RULES,
    )

    system_msg = SystemMessage(
        content=full_prompt + f"\n\nCRITICAL: Implement ALL {tc_count} cases identified."
    )
    instruction = (
        f"I see the source code. STOP REASONING NOW.\n"
        f"TASK: Implement the Approved Test Plan based on the ACTUAL source code provided.\n\n"
        f"STRICT RULES (CRITICAL):\n"
        f"1. **SOURCE FIDELITY**: Do not assume logic that doesn't exist. ONLY assert calls visible in the source code.\n"
        f"2. **EXCEPTION REALISM**: Observe how the source handles errors. Match try/except logic exactly.\n"
        f"3. **IMPORT & PATCHING SAFETY**: Follow the MANDATORY BOILERPLATE ORDER defined in the system prompt. Never put the target file `{ctx.import_path}` or global pip libraries like `requests` into `sys.modules`.\n"
        f"4. **SMART PATCHING**: For globally imported pip libraries, patch at the root: `mocker.patch('requests.get')`.\n"
        f"5. **EXACT COUNT**: Implement EXACTLY {tc_count} standalone Pytest functions.\n"
        f"6. **EXECUTION**: IMMEDIATELY call `write_local_file` with complete code to: {ctx.test_file_path}.\n"
    )
    logger.debug(
        "build_generate_messages full_prompt_len=%s instruction_len=%s",
        len(full_prompt) + len(f"\n\nCRITICAL: Implement ALL {tc_count} cases identified."),
        len(instruction),
    )
    return system_msg, instruction
