from graph.state import AgentState
from shared.config import REPO_PATH
from utils.testing import run_pytest
from utils.paths import get_safe_full_path

def call_executor(state: AgentState):
    # 1. שליפת הנתיב מה-State (שנשמר בשלב ה-Writer)
    test_file_path = state.get("test_file_path")
    
    if not test_file_path:
        print("❌ Error: No test file path found in state.")
        return {"test_run_status": "failed", "last_run_logs": "No test file path provided."}

    print(f"Running pytest on: {test_file_path}")

    # 2. בניית נתיב מלא בצורה בטוחה
    full_path = get_safe_full_path(REPO_PATH, test_file_path)
        
    print(f"Running pytest on full path: {full_path}")

    status, logs = run_pytest(
        full_path=full_path,
        repo_path=REPO_PATH,
        timeout=60,
    )

    # print(f"Running pytest status: {status}")
    # print(f"Running pytest logs: {logs}")
    # 4. עדכון ה-State
    return {
        "test_run_status": status,
        "last_run_logs": logs
    }