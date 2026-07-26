from dotenv import load_dotenv

load_dotenv()

from shared.logging_config import configure_logging

configure_logging()

from langchain_core.messages import HumanMessage
from graph.builder import build_app
from services.code_processor import CodeProcessor
from services.vector_db_service import VectorDBService # הייבוא של הגרף המקומפל מה-Builder
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from shared.constants import resolve_user_task
from shared.graph_config import build_langgraph_run_config
from utils.utils import get_clean_text

# טעינת משתני סביבה (API Keys) — load_dotenv() runs at top of this module


def create_vector_db() -> VectorDBService:
    """Construct VDB at entry points (CLI, run_local); do not use inside graph runners."""
    return VectorDBService()


def build_graph_run_config(
    repo_path: str,
    vdb: VectorDBService,
    processor: CodeProcessor,
    *,
    configurable: dict | None = None,
) -> dict:
    """Backward-compatible alias; see shared.graph_config."""
    return build_langgraph_run_config(
        repo_path, vdb, processor, overrides=configurable
    )


def print_summary_evolution(app, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    
    print("\n" + "="*50)
    print(f"📈 ARCHITECTURE SUMMARY EVOLUTION (Thread: {thread_id})")
    print("="*50)
    
    last_seen_summary = ""
    change_count = 0

    # מעבר על כל ההיסטוריה של ה-State מהישן לחדש
    for state in app.get_state_history(config):
        current_summary = state.values.get("architecture_summary", "")
        
        # מדפיסים רק אם יש סיכום ורק אם הוא השתנה מהפעם הקודמת
        if current_summary and current_summary != last_seen_summary:
            change_count += 1
            print(f"\nגירסה {change_count} | Node: {state.next or 'END'}")
            print("-" * 20)
            print(current_summary)
            print("-" * 50)
            last_seen_summary = current_summary

    if change_count == 0:
        print("לא נמצאו שינויים בסיכום ב-Thread הזה.")
    else:
        print(f"\n✅ סהקה: נמצאו {change_count} גרסאות של הסיכום.")

def print_current_db_state(app, thread_id):
     config = {"configurable": {"thread_id": thread_id}}
     state = app.get_state(config)
    
     print("\n" + "="*50)
     print(f"📊 CURRENT DB STATE (Thread: {thread_id})")
     print("="*50)
    

     messages = state.values.get("messages", [])
     print(f"📂 messages ({len(messages)}): {messages}")
     
     test_chunks = state.values.get("test_chunks", [])
     print(f"📂 test_chunks ({len(test_chunks)}): {test_chunks}")

     # הדפסת רשימת הקבצים שנחקרו
     target_file_code = state.values.get("target_file_code", [])
     print(f"📂 target_file_code  ({len(target_file_code)}): {target_file_code}")

     # הדפסת רשימת הקבצים שנחקרו
     test_plan = state.values.get("test_plan", [])
     print(f"📂 test_plan: {test_plan}")

     review_completed = state.values.get("review_completed", [])
     print(f"📂 review_completed: {review_completed}")

     target_file = state.values.get("target_file", [])
     print(f"📂 target_file: {target_file}")

     # הדפסת סיכום הארכיטקטורה
     summary = state.values.get("architecture_summary", "No summary found.")
     print(f"\n📝 Architecture Summary:\n{summary}")
     print("="*50 + "\n")


def run_test_system_stream(
    repo_path: str,
    vdb: VectorDBService,
    processor: CodeProcessor | None = None,
    user_task: str | None = None,
    configurable: dict | None = None,
):
    console = Console()
    app, conn = build_app()
    try:
        return _run_test_system_stream_impl(
            console,
            app,
            repo_path,
            vdb=vdb,
            processor=processor,
            user_task=user_task,
            configurable=configurable,
        )
    finally:
        conn.close()
        print("Cleanup: SQLite connection closed.")


def _run_test_system_stream_impl(
    console,
    app,
    repo_path: str,
    vdb: VectorDBService,
    processor: CodeProcessor | None = None,
    user_task: str | None = None,
    configurable: dict | None = None,
):
    proc = processor or CodeProcessor()
    config = build_graph_run_config(
        repo_path,
        vdb,
        proc,
        configurable=configurable,
    )
    thread_id = config["configurable"]["thread_id"]

    console.print(f"\n🚀 [bold]Starting Test Agent System[/bold] (Thread: {thread_id})", style="blue")
    console.print("-" * 60)

    user_task = resolve_user_task(user_task)

    # עדכון ה-State הראשוני
    app.update_state(config, {
        "user_input": user_task, 
        "messages": [HumanMessage(content=user_task)],
        # אנחנו מאתחלים את הסטטוס ל-pending כדי שה-Writer ידע שזה סבב ראשון
        "test_run_status": "pending"
    },
     )

    console.print(f"🔍 [bold yellow]Analyzing project for task:[/bold yellow] '{user_task}'...\n")

    # 2. Streaming - מעבר על כל ה-Nodes בגרף
    for event in app.stream(None, config, stream_mode="updates"):
        for node_name, output in event.items():
            console.print(f"\n[bold reverse] NODE: {node_name.upper()} [/bold reverse]")
            
            # --- RESEARCHER ---
            if node_name == "researcher":
                console.print("📡 Researcher is searching Vector DB for context...")
            
            # --- SUMMARIZER ---
            elif node_name == "summarizer":
                console.print(f"📝 Summary updated. Metadata extracted.")
            
            # --- DESIGNER / REVIEWER ---
            elif node_name in ["designer", "reviewer"]:
                if "messages" in output:
                    last_msg = output["messages"][-1]
                    # שימוש בפונקציית החילוץ כדי למנוע את קריסת Rich
                    safe_content = get_clean_text(last_msg.content)
                    
                    title = "🎨 Draft Test Plan" if node_name == "designer" else "🛡️ Reviewed Final Plan"
                    style = "magenta" if node_name == "designer" else "green"
                    
                    if safe_content:
                        console.print(Panel(safe_content, title=title, border_style=style))
                    
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        console.print(f"🛠️ Calling tools: {[t['name'] for t in last_msg.tool_calls]}")

            # --- FINAL_CLEANER ---
            elif node_name == "final_cleaner":
                target = output.get("target_file", "Unknown")
                console.print(f"🧹 [bold cyan]State Cleaned.[/bold cyan]")
                console.print(f"📂 Target identified: [bold white]{target}[/bold white]")
                console.print(f"🗑️ History wiped. Ready for implementation.")

            # --- WRITER ---
            elif node_name == "writer":
                if "messages" in output:
                    last_msg = output["messages"][-1]
                    safe_content = get_clean_text(last_msg.content)
                    
                    # הצגת פעולות הכלים
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        for tool in last_msg.tool_calls:
                            if tool['name'] == "read_local_file":
                                console.print(f"📖 [yellow]Reading source code:[/yellow] {tool['args'].get('file_path')}")
                            elif tool['name'] == "write_local_file":
                                console.print(f"💾 [green]Saving test file:[/green] {tool['args'].get('file_path')}")
                    
                    # הצגת קוד ה-Python שנוצר עם Markdown
                    if safe_content:
                        console.print(Panel(Markdown(safe_content), title="💻 Generated Python Code", border_style="blue"))

             # --- EXECUTOR (סוכן הריצה) ---
            elif node_name == "executor":
                status = output.get("test_run_status", "unknown")
                logs = output.get("last_run_logs", "")
                
                if status == "passed":
                    console.print(f"✅ [bold green]Pytest Passed![/bold green]")
                    console.print(Panel(logs, title="📊 Execution Logs", border_style="green"))
                else:
                    console.print(f"❌ [bold red]Pytest Failed![/bold red]")
                    # מציגים רק את סוף הלוג כדי לא להציף את המסך
                    short_logs = "\n".join(logs.splitlines()[-15:]) 
                    console.print(Panel(short_logs, title="⚠️ Failure Logs (Last 15 lines)", border_style="red"))   

    # 3. סיום - מחוץ ללולאת ה-stream
    final_state = app.get_state(config).values
    final_status = final_state.get("test_run_status", "unknown")

    console.print("\n")
    if final_status == "passed":
        console.print(Panel(
            f"🎊 [bold green]SUCCESS: ALL TESTS PASSED![/bold green]\n"
            f"The tests were generated, executed, and verified.\n"
            f"Location: [italic]{final_state.get('test_file_path')}[/italic]",
            expand=False, 
            border_style="bold green"
        ))
    else:
        console.print(Panel(
            f"⚠️ [bold yellow]WORKFLOW STOPPED WITH ISSUES[/bold yellow]\n"
            f"The system finished, but the final test status is: [bold red]{final_status}[/bold red].\n"
            f"Check the logs above for debugging.",
            expand=False, 
            border_style="bold red"
        ))


def run_ingest_only(
    repo_path: str,
    ingest: str,
    vdb: VectorDBService,
) -> None:
    """Ingest seed/source/both into Chroma (+ BM25 on source). No graph run."""
    from ingest import IngestMode, run_both_ingestion, run_ingestion_for_repo

    if ingest == "both":
        run_both_ingestion(vdb, repo_root=repo_path)
    elif ingest == "seed":
        run_ingestion_for_repo(vdb, IngestMode.SEED, repo_root=repo_path)
    elif ingest == "source":
        run_ingestion_for_repo(vdb, IngestMode.SOURCE, repo_root=repo_path)
    else:
        raise ValueError(f"Unknown ingest mode: {ingest!r}")


def run_agent_only(
    repo_path: str,
    vdb: VectorDBService,
    *,
    processor: CodeProcessor | None = None,
    user_task: str | None = None,
    configurable: dict | None = None,
) -> None:
    """Run the LangGraph agent (streaming) only."""
    run_test_system_stream(
        repo_path,
        vdb,
        processor=processor,
        user_task=user_task,
        configurable=configurable,
    )


def run_pipeline(
    repo_path: str,
    vdb: VectorDBService,
    *,
    ingest: str | None = None,
    processor: CodeProcessor | None = None,
    user_task: str | None = None,
    configurable: dict | None = None,
) -> None:
    """
    Optional ingest then agent run. No CLI — for run_local.py and notebooks.

    ingest: None | \"both\" | \"seed\" | \"source\" (None = agent only)
    """
    if ingest is not None:
        run_ingest_only(repo_path, ingest, vdb)
    run_agent_only(
        repo_path,
        vdb,
        processor=processor,
        user_task=user_task,
        configurable=configurable,
    )


if __name__ == "__main__":
    import argparse

    from shared.repo_cli import add_repo_path_argument, resolve_repo_path

    parser = argparse.ArgumentParser(description="Run the agentic test system.")
    add_repo_path_argument(parser)
    parser.add_argument(
        "--task",
        default=None,
        help="Agent task prompt (default: USER_TASK env or built-in analysis_service request).",
    )
    args = parser.parse_args()
    repo_path = resolve_repo_path(args.repo_path)
    user_task = resolve_user_task(args.task)

    from shared.startup_checks import validate_runtime_startup

    validate_runtime_startup(repo_path)

    vdb = create_vector_db()
    run_test_system_stream(repo_path, vdb, user_task=user_task)