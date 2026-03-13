import os
from langchain_core.tools import tool

from shared.config import REPO_PATH
from utils.utils import get_safe_full_path

@tool
def write_local_file(file_path: str, content: str) -> str:
    """
    Writes content to a local file. 
    Path must be relative to project root.
    """
    try:
 
        full_path = get_safe_full_path(REPO_PATH, file_path)

        print(f"\n💾 [TOOL CALL] Writing file: {full_path}")

        # 3. חילוץ התיקייה ויצירתה (mkdir -p)
        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        # 4. כתיבת התוכן
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"SUCCESS: File written to absolute path: {full_path}"
    
    except Exception as e:
        return f"Error writing file: {str(e)}"



WRITER_TOOLS = [write_local_file]    