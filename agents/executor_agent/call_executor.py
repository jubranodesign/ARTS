import logging
import os

from langgraph.graph.state import RunnableConfig

from graph.state import AgentState
from utils.paths import get_safe_full_path
from utils.testing import run_pytest

logger = logging.getLogger(__name__)


def call_executor(state: AgentState, config: RunnableConfig):
    repo_path = config["configurable"]["repo_path"]
    # 1. שליפת הנתיב מה-State (שנשמר בשלב ה-Writer)
    test_file_path = state.get("test_file_path")
    current_attempts = state.get("attempts", 0)
    target_file = state.get("target_file") 

    if not test_file_path:
        logger.error("No test file path found in state.")
        return {"test_run_status": "failed", "last_run_logs": "No test file path provided."}

    logger.info("Running pytest on: %s", test_file_path)

    source_service_dir = os.path.dirname(target_file) 

    # 2. בונים נתיב אבסולוטי מלא לתיקיית קוד המקור בתוך ה-Repo
    full_service_path = os.path.abspath(os.path.join(repo_path, source_service_dir))

    # 3. מייצרים סביבת ריצה דינמית (Environment)
    env = os.environ.copy()

    # 4. מזריקים ל-PYTHONPATH את השורש ואת התיקייה המקורית של השירות (Source Service Dir)
    # משתמשים בנקודתיים (:) בלינוקס/מקינטוש או נקודה-פסיק (;) בווינדows
    path_separator = ";" if os.name == "nt" else ":"
    env["PYTHONPATH"] = f"{repo_path}{path_separator}{full_service_path}{path_separator}{env.get('PYTHONPATH', '')}"

    # חילוץ נתיב מלא לקובץ הטסט האמיתי כדי להריץ רק אותו
    full_test_file_path = get_safe_full_path(repo_path, test_file_path)

    logger.info("Dynamically injected source to PYTHONPATH: %s", full_service_path)
    logger.info("Running pytest on full path: %s", full_test_file_path)

    # 5. מריצים את ה-Pytest על קובץ הטסט, עם ה-env שמכיר את קוד המקור!
    status, logs = run_pytest(
        full_path=full_test_file_path, # <-- מריצים את קובץ הטסט!
        repo_path=repo_path,
        env=env,
        timeout=60,
    )

    return {
        "test_run_status": status,
        "last_run_logs": logs,
        "attempts": current_attempts + 1 
    }
