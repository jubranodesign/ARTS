"""Routing functions for the LangGraph workflow (conditional edges)."""

from langgraph.graph import END

from graph.state import AgentState


def route_after_input(state: AgentState):
    if state.get("user_input"):
        return "researcher"
    return END


def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "finish"


def route_after_cleaner(state: AgentState):
    if state.get("review_completed"):
        print("🔄 Cleaner -> Routing to WRITER")
        return "to_writer"
    print("🔄 Cleaner -> Routing to REVIEWER")
    return "to_reviewer"


def should_continue_after_test(state: AgentState):
    if state["test_run_status"] == "passed":
        print("should_continue_after_test. passed")
        return "finish"
    print("should_continue_after_test. fix_code")
    return "fix_code"
