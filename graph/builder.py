import atexit
import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

# ייבוא החלקים שבנינו
from agents.designer_agent.call_reviewer import call_reviewer
from agents.designer_agent.final_cleaner_designer import final_cleaner_designer
from agents.designer_agent.update_investigated_files import update_investigated_files
from agents.designer_agent.call_designer import call_designer
from agents.executor_agent.call_executor import call_executor
from agents.researcher_agent.wait_for_task import wait_for_task
from agents.designer_agent.tools import DESIGNER_TOOLS
from agents.writer_agent.final_cleaner_writer import final_cleaner_writer
from agents.writer_agent.call_writer import call_writer
from agents.writer_agent.tools import WRITER_TOOLS
from graph.state import AgentState
from agents.researcher_agent.call_researcher import call_researcher
from agents.researcher_agent.summarize_architecture import summarize_architecture
from agents.researcher_agent.tools import RESEARCHER_TOOLS

# 1. הגדרת ה-Workflow (ה-StateGraph)
# אנחנו אומרים לו באיזה מבנה נתונים (State) להשתמש
workflow = StateGraph(AgentState)

# 2. הוספת ה-Nodes לגרף
workflow.add_node("wait_for_task", wait_for_task) # צומת עם Interrupt
workflow.add_node("researcher", call_researcher)
workflow.add_node("researcher_tools", ToolNode(RESEARCHER_TOOLS))
workflow.add_node("summarizer", summarize_architecture)
workflow.add_node("designer", call_designer)
workflow.add_node("designer_tools", ToolNode(DESIGNER_TOOLS))
workflow.add_node("update_investigated_files", update_investigated_files)
workflow.add_node("reviewer", call_reviewer)
workflow.add_node("reviewer_tools", ToolNode(DESIGNER_TOOLS))
workflow.add_node("final_cleaner_designer", final_cleaner_designer)
workflow.add_node("writer", call_writer)
workflow.add_node("writer_tools", ToolNode(DESIGNER_TOOLS + WRITER_TOOLS))
workflow.add_node("final_cleaner_writer", final_cleaner_writer)
workflow.add_node("executor", call_executor)

# 3. הגדרת נקודת הכניסה
workflow.set_entry_point("wait_for_task")

# 1. פונקציית הניתוב
def route_after_input(state: AgentState):
    # אם המשתמש הזין בקשה, נעבור לעיצוב הטסט
    if state.get("user_input"):
        return "researcher"
    # אם אין קלט (למשל סגרת את התוכנית), פשוט נסיים
    return END

# 2. חיבור בגרף
workflow.add_conditional_edges(
    "wait_for_task",     # הצומת ממנו יוצאים
    route_after_input,   # הפונקציה שמחליטה
    {
        "researcher": "researcher", 
        END: END                        
    }
)

# 4. פונקציית העזר לניתוב (should_continue)
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # אם המודל ביקש להפעיל כלי, נמשיך ל-ToolNode
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    # אם לא, נעבור לסיכום ונסיים את סבב המחקר
    return "finish"

# 5. הגדרת הקשתות (Edges)
workflow.add_conditional_edges(
    "researcher",
    should_continue,
    {
        "continue": "researcher_tools",
        "finish": "summarizer"
    }
)

# סגירת הלולאה הפנימית של המחקר
workflow.add_edge("researcher_tools", "researcher")

workflow.add_edge("summarizer", "designer")
workflow.add_edge("designer_tools", "update_investigated_files")
workflow.add_edge("update_investigated_files", "designer")

workflow.add_conditional_edges(
    "designer",
    should_continue,
    {
        "continue": "designer_tools",
        "finish": "reviewer"
    }
)


workflow.add_conditional_edges(
    "reviewer",
    should_continue,
    {
        "continue": "reviewer_tools", # ה-Reviewer משתמש באותם כלים לקריאת קבצים
        "finish": "final_cleaner_designer" # או "writer"
    }
)

workflow.add_edge("reviewer_tools", "reviewer")
workflow.add_edge("final_cleaner_designer", "writer")

# 2. הוספת קצה מותנה (Conditional Edge) מהכותב
# הוא יבדוק אם יש Tool Calls - אם כן ילך לכלים, אם לא יסיים
workflow.add_conditional_edges(
    "writer",
    should_continue, # פונקציה שבודקת אם יש tool_calls בהודעה האחרונה
    {
        "continue": "writer_tools",
        "finish": "final_cleaner_writer"
    }
)

workflow.add_edge("writer_tools", "writer")
workflow.add_edge("final_cleaner_writer", "executor")


def should_continue_after_test(state: AgentState):
    # ה-Edge בודק את הסטטוס שעדכנו הרגע ב-Executor
    if state["test_run_status"] == "passed":
        print("should_continue_after_test. passed")
        return "finish" # הטסטים עברו, אפשר לסיים
    else:
        print("should_continue_after_test. fix_code")
        return "fix_code" # הטסטים נכשלו, חוזרים ל-Writer/Debugger


workflow.add_conditional_edges(
    "executor",
    should_continue_after_test, # פונקציה שבודקת אם יש tool_calls בהודעה האחרונה
    {
        "fix_code": "writer",
        "finish": END
    }
)

# 6. חיבור ה-Persistence (SQLite) וקומפילציה
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)

def cleanup():
    conn.close()
    print("Cleanup: SQLite connection closed.")

# רישום הפונקציה שתרוץ בכיבוי המערכת
atexit.register(cleanup)

memory = SqliteSaver(conn)
app = workflow.compile(checkpointer=memory, interrupt_before=["wait_for_task"])