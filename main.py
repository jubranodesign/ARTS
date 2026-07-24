import os
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from graph.builder import app
from services.code_processor import CodeProcessor
from services.vector_db_service import VectorDBService # הייבוא של הגרף המקומפל מה-Builder
from shared.config import REPO_PATH
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from utils.utils import get_clean_text

# טעינת משתני סביבה (API Keys)
load_dotenv()


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

# def run_test_system_stream():
#     vdb_instance = VectorDBService()
#     thread_id = "test_invoke_session_001"
#     config = {"vdb": vdb_instance, "configurable": {"thread_id": thread_id, "model_provider": "groq"}}
   
#     print(f"🚀 Starting Test Agent System (Thread: {thread_id})")
#     print("-" * 50)

#     # 2. הרצה ראשונית
#     app.invoke({"messages": []}, config=config)

#     # 3. המשימה
#     user_task = "Write unit tests for the file scraper_service/scraper_api.py"
#     app.update_state(config, {"user_input": user_task, "messages": [HumanMessage(content=user_task)]}, as_node="wait_for_task")

#     print(f"\n🔍 Analyzing project for task: '{user_task}'...")

#     # 4. Streaming - הדפסה לכל Node
#     for event in app.stream(None, config, stream_mode="updates"):
#         for node_name, output in event.items():
#             print(f"\n[NODE: {node_name.upper()}]")
            
#             if node_name == "researcher":
#                 print(f"📡 Researcher is looking for clues in Vector DB...")
            
#             elif node_name == "summarizer":
#                 summary_val = output.get('architecture_summary', "No summary provided")
#                 print(f"📝 Summary updated. Confidence: {str(summary_val)}...")
            
#             elif node_name == "designer":
#                 if "messages" in output:
#                     last_msg = output["messages"][-1]
#                     # הדפסת התוכן של הדיזיינר (הטיוטה)
#                     if last_msg.content:
#                         print(f"🎨 Designer Content:\n{last_msg.content}")
#                     # הדפסת הכלים שלו
#                     if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
#                         print(f"🛠️ Designer is calling tools: {[t['name'] for t in last_msg.tool_calls]}")

#             elif node_name == "reviewer":
#                 if "messages" in output:
#                     last_msg = output["messages"][-1]
#                     # הדפסת התוכן של הריביוור (התיקונים/התוכנית הסופית)
#                     if last_msg.content:
#                         print(f"🛡️ Reviewer Content:\n{last_msg.content}")
#                     # הדפסת הכלים שלו
#                     if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
#                         print(f"🛠️ Reviewer is calling tools: {[t['name'] for t in last_msg.tool_calls]}")

#             elif node_name == "update_investigated_files":
#                 print(f"📂 Files investigated so far: {output.get('investigated_files')}")

#     console = Console()
#     # 5. הצגת התוצאה הסופית
#     final_state = app.get_state(config)
#     final_messages = final_state.values.get("messages", [])
    
#     if final_messages:
#         # חילוץ תוכן מהודעת ה-AI האחרונה שיש בה טקסט (למקרה שהאחרונה היא קריאת כלי ריקה)
#         target_content = ""
#         for msg in reversed(final_messages):
#             if isinstance(msg, AIMessage) and msg.content:
#                 target_content = msg.content
#                 break
        
#         if target_content:
#             full_text = "".join([item.get("text", "") for item in target_content if item.get("type") == "text"]) if isinstance(target_content, list) else target_content
#             console.print("\n")
#             console.print(Panel("✅ [bold green]FINAL TEST PLAN GENERATED[/bold green]", expand=False))
#             console.print(Markdown(full_text))
#             console.print("="*50)


def run_test_system_stream():
    console = Console()

    vdb_instance = VectorDBService()
    processor = CodeProcessor()
    thread_id = "test_invoke_session_001"
    config = {
        "configurable": {
            "thread_id": thread_id,
            "model_provider": "mistral",
            "ground_truth": "The scraper service orchestrates data pull via fetch_studies and persists it using a session context manager with a single commit after the loop. Key dependencies are common.db and common.repositories.",
            "vdb": vdb_instance,
            "processor": processor,
            "repo_path": REPO_PATH,
        }
    }

    console.print(f"\n🚀 [bold]Starting Test Agent System[/bold] (Thread: {thread_id})", style="blue")
    console.print("-" * 60)

    # 1. המשימה
    # user_task = "Write unit tests for the file scraper_service/scraper.py"
    user_task = "Write unit tests for the file analysis_service/analysis.py"
    
    # user_task = "Analyze the database commit logic in the scraper."

    # עדכון ה-State הראשוני
    app.update_state(config, {
        "user_input": user_task, 
        "messages": [HumanMessage(content=user_task)],
        # אנחנו מאתחלים את הסטטוס ל-pending כדי שה-Writer ידע שזה סבב ראשון
        "test_run_status": "pending"
    },
    #  as_node="wait_for_task"
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

            # --- UPDATE_INVESTIGATED_FILES ---
            elif node_name == "update_investigated_files":
                console.print(f"📂 Investigated so far: {output.get('investigated_files')}")

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

    # 3. סיום
    # console.print("\n")
    # console.print(Panel(
    #     f"✅ [bold green]WORKFLOW COMPLETE[/bold green]\n"
    #     f"The tests have been generated and saved.\n"
    #     f"You can now run [bold]pytest tests/[/bold] to verify.",
    #     expand=False, 
    #     border_style="bold green"
    # ))
    # 3. סיום - מחוץ ללולאת ה-stream
    # נשלוף את ה-state הסופי כדי לדעת מה קרה
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


def run_test_system():
    # 1. הגדרות בסיס
    vdb_instance = VectorDBService()
    processor = CodeProcessor()
    thread_id = "test_invoke_session_001"
    config = {
        "configurable": {
            "thread_id": thread_id,
            "model_provider": "groq",
            "vdb": vdb_instance,
            "processor": processor,
            "repo_path": REPO_PATH,
        }
    }
    user_task = "Write a comprehensive test for the scraper service, focusing on data validation."

    print(f"🚀 Starting Test Agent System (STRICT INVOKE MODE)")
    print(f"Target Task: {user_task}")
    print("-" * 50)

    try:
        # 2. הרצה ראשונית עד ה-Interrupt (wait_for_task)
        # אנחנו שולחים הודעה ריקה רק כדי להביא את הגרף לנקודת העצירה
        app.invoke({"messages": []}, config=config)

        # 3. הזרקת המשימה לתוך ה-State
        # חשוב: אנחנו מזריקים גם את האובייקט HumanMessage וגם את הסטרינג user_input
        print("📥 Injecting task and human message into state...")
        app.update_state(
            config, 
            {
                "user_input": user_task, 
                "messages": [HumanMessage(content=user_task)]
            }, 
            as_node="wait_for_task"
        )

        # 4. הרצה מהעצירה ועד הסוף
        # שליחת None אומרת לגרף: "תמשיך מהמקום שבו עצרת ב-thread_id הזה"
        print("⏳ Running agents (Researcher -> Summarizer -> Designer)...")
        final_result = app.invoke(None, config=config)

        # 5. הצגת התוצאה
        messages = final_result.get("messages", [])
        if messages:
            last_msg = messages[-1]
            print("\n" + "="*50)
            print("✅ FINAL DESIGNER OUTPUT:")
            print("="*50)
            print(last_msg.content)
            print("="*50)
        else:
            print("⚠️ System finished but no messages were found in state.")

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during invoke: {e}")
        # אם יש שגיאה, ננסה לשלוף את המצב האחרון לדיבאג
        current_state = app.get_state(config)
        print(f"Last Node Reached: {current_state.next}")


if __name__ == "__main__":
    #  run_test_system()
    run_test_system_stream()

    #  config = {"configurable": {"thread_id": "test_invoke_session_001"}}
    #  messages = app.get_state(config).values["messages"]
    #  app.update_state(config, {
    #  "test_chunks": "",
    #  "messages": [RemoveMessage(id=m.id) for m in messages]
    # # "investigated_files": {"scraper_service/scraper_api.py"} 
    #  })
    #  print_current_db_state(app,"test_invoke_session_001")
    # print_summary_evolution(app,"test_invoke_session_001")