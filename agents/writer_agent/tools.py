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


def patch_test_code(file_path: str, patch_content: str) -> str:
    """
    Applies a Search/Replace patch to a file using a safe path.
    Format of patch_content:
    <<<<<<< SEARCH
    old code
    =======
    new code
    >>>>>>> REPLACE
    """
    print(f"patch_test_code patch_content: {patch_content}")
    try:
        # שימוש בפונקציית העזר כדי לקבל נתיב בטוח ומלא
        full_path = get_safe_full_path(REPO_PATH, file_path)
        
        if not os.path.exists(full_path):
            return f"Error: File {file_path} (Full path: {full_path}) not found."

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # חילוץ חלקי החיפוש וההחלפה מהפלט של ה-AI
        if "<<<<<<< SEARCH" not in patch_content or "=======" not in patch_content:
            return "Error: Invalid patch format. Missing <<<<<<< SEARCH or =======."

        try:
            search_part = patch_content.split("<<<<<<< SEARCH")[1].split("=======")[0].strip()
            replace_part = patch_content.split("=======")[1].split(">>>>>>> REPLACE")[0].strip()
        except IndexError:
            return "Error: Could not parse SEARCH/REPLACE blocks. Check the format."

        # בדיקה שהקוד לחיפוש אכן קיים בקובץ
        if search_part not in content:
            return "Error: The SEARCH block was not found in the file. Ensure the snippet matches EXACTLY (including indentation)."

        # ביצוע ההחלפה
        new_content = content.replace(search_part, replace_part)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return f"Successfully patched {file_path}."
    
    except Exception as e:
        return f"An error occurred during patching: {str(e)}"


WRITER_TOOLS = [write_local_file, patch_test_code]    