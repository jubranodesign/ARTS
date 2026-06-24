import atexit
import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

from agents.designer_agent.call_reviewer import call_reviewer
from agents.designer_agent.final_cleaner_designer import final_cleaner_designer
from agents.designer_agent.update_investigated_files import update_investigated_files
from agents.designer_agent.call_designer import call_designer
from agents.executor_agent.save_test_node import save_test_node
from agents.executor_agent.call_executor import call_executor
from agents.researcher_agent.wait_for_task import wait_for_task
from agents.shared.agent_tools import AGENT_TOOLS
from agents.writer_agent.final_cleaner_writer import final_cleaner_writer
from agents.writer_agent.call_writer import call_writer
from agents.writer_agent.tools import WRITER_TOOLS
from graph.state import AgentState
from agents.researcher_agent.call_researcher import call_researcher
from agents.researcher_agent.summarize_architecture import summarize_architecture
from agents.researcher_agent.tools import RESEARCHER_TOOLS
from graph.routes import (
    route_after_input,
    route_after_cleaner,
    should_continue,
    should_continue_after_test,
)

workflow = StateGraph(AgentState)

workflow.add_node("wait_for_task", wait_for_task)
workflow.add_node("researcher", call_researcher)
workflow.add_node("researcher_tools", ToolNode(RESEARCHER_TOOLS))
workflow.add_node("summarizer", summarize_architecture)
workflow.add_node("designer", call_designer)
workflow.add_node("designer_tools", ToolNode(AGENT_TOOLS))
workflow.add_node("update_investigated_files", update_investigated_files)
workflow.add_node("reviewer", call_reviewer)
workflow.add_node("reviewer_tools", ToolNode(AGENT_TOOLS))
workflow.add_node("final_cleaner_designer", final_cleaner_designer)
workflow.add_node("writer", call_writer)
workflow.add_node("writer_tools", ToolNode(AGENT_TOOLS + WRITER_TOOLS))
workflow.add_node("final_cleaner_writer", final_cleaner_writer)
workflow.add_node("executor", call_executor)
workflow.add_node("save_successful_test", save_test_node)

workflow.set_entry_point("wait_for_task")

workflow.add_conditional_edges(
    "wait_for_task",
    route_after_input,
    {
        "researcher": "researcher",
        END: END,
    },
)

workflow.add_conditional_edges(
    "researcher",
    should_continue,
    {
        "continue": "researcher_tools",
        "finish": "summarizer",
    },
)

workflow.add_edge("researcher_tools", "researcher")

workflow.add_edge("summarizer", "designer")
workflow.add_edge("designer_tools", "designer")
# workflow.add_edge("designer_tools", "update_investigated_files")
# workflow.add_edge("update_investigated_files", "designer")

workflow.add_conditional_edges(
    "designer",
    should_continue,
    {
        "continue": "designer_tools",
        "finish": "final_cleaner_designer",
    },
)

workflow.add_conditional_edges(
    "reviewer",
    should_continue,
    {
        "continue": "reviewer_tools",
        "finish": "final_cleaner_designer",
    },
)

workflow.add_conditional_edges(
    "final_cleaner_designer",
    route_after_cleaner,
    {
        "to_reviewer": "reviewer",
        "to_writer": "writer",
    },
)

workflow.add_edge("reviewer_tools", "reviewer")

workflow.add_conditional_edges(
    "writer",
    should_continue,
    {
        "continue": "writer_tools",
        "finish": "final_cleaner_writer",
    },
)

workflow.add_edge("writer_tools", "writer")
workflow.add_edge("final_cleaner_writer", "executor")

workflow.add_conditional_edges(
    "executor",
    should_continue_after_test,
    {
        "fix_code": "writer",
        "finish": "save_successful_test",
    },
)

workflow.add_edge("save_successful_test", END)

conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)


def cleanup():
    conn.close()
    print("Cleanup: SQLite connection closed.")


atexit.register(cleanup)

memory = SqliteSaver(conn)
app = workflow.compile(checkpointer=memory, interrupt_before=["wait_for_task"])
# app = workflow.compile(interrupt_before=["wait_for_task"])
