import os
import subprocess
import sys

from graph.state import AgentState

import subprocess

from shared.config import REPO_PATH

def call_executor(state: AgentState):
    # 1. שליפת הנתיב מה-State (שנשמר בשלב ה-Writer)
    test_file_path = state.get("test_file_path")
    
    if not test_file_path:
        print("❌ Error: No test file path found in state.")
        return {"test_run_status": "failed", "last_run_logs": "No test file path provided."}

    print(f"Running pytest on: {test_file_path}")

        # 2. חיבור ל-REPO_PATH כדי לוודא שכותבים למקום הנכון
    full_path = os.path.join(REPO_PATH, test_file_path)
    full_path = os.path.normpath(full_path)    
        
    print(f"Running pytest on full path: {full_path}")

    # 2. הרצת pytest דרך subprocess
    # capture_output=True לוכד את ה-stdout (דיווח) וה-stderr (שגיאות מערכת)
    # text=True מבטיח שנקבל מחרוזת (String) ולא בייטים
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", full_path, "--tb=short"], 
            cwd=REPO_PATH, # חשוב מאוד כדי שה-imports יעבדו
            capture_output=True, 
            text=True,
            timeout=60
        )
        
        # 3. ניתוח התוצאות
        # returncode == 0 אומר שכל הטסטים עברו (Passed)
        if result.returncode == 0:
            status = "passed"
            logs = result.stdout
        else:
            status = "failed"
            # אנחנו מאחדים את stdout ו-stderr כדי שהסוכן יראה את התמונה המלאה של הכישלון
            logs = result.stdout + "\n" + result.stderr
            
    except subprocess.TimeoutExpired:
        status = "failed"
        logs = "Timeout: Pytest execution took too long (possible infinite loop)."
    except Exception as e:
        status = "failed"
        logs = f"Execution Error: {str(e)}"

       
    # print(f"Running pytest status: {status}")
    # print(f"Running pytest logs: {logs}")
    # 4. עדכון ה-State
    return {
        "test_run_status": status,
        "last_run_logs": logs
    }