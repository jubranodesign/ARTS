import logging

from langgraph.graph.state import RunnableConfig

from agents.shared.agent_tools import AGENT_TOOLS
from agents.writer_agent.tools import WRITER_TOOLS
from agents.writer_agent.writer_logic import (
    build_generate_messages,
    build_repair_messages,
    build_writer_context,
    handle_post_tool_success,
)
from graph.state import AgentState
from shared.config import setup_node_llm
from utils.utils import build_agent_messages

logger = logging.getLogger(__name__)


def call_writer(state: AgentState, config: RunnableConfig):
    post_tool_update = handle_post_tool_success(state)
    if post_tool_update is not None:
        return post_tool_update

    llm = setup_node_llm(config, AGENT_TOOLS + WRITER_TOOLS)
    ctx = build_writer_context(state, config)

    if state.get("test_run_status") == "failed":
        system_msg, instruction = build_repair_messages(ctx, state)
    else:
        system_msg, instruction = build_generate_messages(ctx, state)

    input_messages = build_agent_messages(
        state=state,
        system_msg=system_msg,
        target_file=ctx.target_file,
        execute_instruction=instruction,
        llm=llm,
    )

    logger.debug(
        "Writer node messages count=%s sequence_types=%s",
        len(input_messages),
        [type(m).__name__ for m in input_messages],
    )

    response = llm.invoke(input_messages)
    return {"messages": [response], "test_file_path": ctx.test_file_path}
