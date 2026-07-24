import os
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from utils.utils import get_safe_full_path

@tool
def read_local_file(file_path: str, config: RunnableConfig) -> str:
    """Reads a file from the project. Path must be relative to project root."""
    try:
        repo_path = config["configurable"]["repo_path"]
        full_path = get_safe_full_path(repo_path, file_path)

        print(f"\n📖 [TOOL CALL] Reading file: {full_path}")

        if not os.path.exists(full_path):
            # החזרת שגיאה מפורטת שתעזור לו לתקן את הנתיב
            return f"Error: File not found. Tried to access: {full_path}. Ensure your path is relative to the project root."

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

       
        # כאן ה-Response הופך ל"חכם":
        # אנחנו מחזירים אישור על המיקום המדויק יחד עם התוכן
        response = f"SUCCESS: File read from absolute path: {full_path}\n"
        response += content
        print(f"\n📖 [TOOL CALL] Reading file response: {response}") 

        return response
        
    except Exception as e:
        return f"Error: {str(e)}"


AGENT_TOOLS = [read_local_file]


