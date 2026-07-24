import os
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from utils.utils import get_safe_full_path

@tool
def write_local_file(file_path: str, content: str, config: RunnableConfig) -> str:
    """
    Writes content to a local file. 
    Path must be relative to project root.
    """
    try:
 
        repo_path = config["configurable"]["repo_path"]
        full_path = get_safe_full_path(repo_path, file_path)

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


@tool
def patch_test_code(file_path: str, patch_content: str, config: RunnableConfig) -> str:
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
        # שימוש בפונקציית העזר לקבלת נתיב מלא ובטוח
        repo_path = config["configurable"]["repo_path"]
        full_path = get_safe_full_path(repo_path, file_path)
        
        if not os.path.exists(full_path):
            return f"Error: File {file_path} (Full path: {full_path}) not found."

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # ולידציה בסיסית על הפורמט של הבלוק
        if "<<<<<<< SEARCH" not in patch_content or "=======" not in patch_content or ">>>>>>> REPLACE" not in patch_content:
            return "Error: Invalid patch format. Missing <<<<<<< SEARCH, =======, or >>>>>>> REPLACE."

        try:
            # 1. חילוץ בסיסי של הבלוקים מהסוכן
            search_part = patch_content.split("<<<<<<< SEARCH")[1].split("=======")[0].strip('\r\n')
            replace_part = patch_content.split("=======")[1].split(">>>>>>> REPLACE")[0].strip('\r\n')
            
            # 2. נורמליזציה של ירידות שורה למניעת הבדלי Windows/Linux (\r\n מול \n)
            content = content.replace("\r\n", "\n")
            search_part = search_part.replace("\r\n", "\n")
            replace_part = replace_part.replace("\r\n", "\n")

            # 3. ניקוי רווחים מיותרים בלתי נראים מסוף כל שורה בבלוק החיפוש
            search_part = "\n".join([line.rstrip() for line in search_part.split("\n")])
            
        except IndexError:
            return "Error: Could not parse SEARCH/REPLACE blocks. Check the format."

        # 4. מנגנון בדיקה חכם והחלפה גמישה
        if search_part in content and search_part != "":
            # מקרה אידיאלי: הבלוק המלא נמצא בדיוק כפי שהוא תו לתו
            new_content = content.replace(search_part, replace_part, 1)
        else:
            # 🎯 המנגנון הגמיש החדש: הבלוק המלא לא נמצא (למשל כי ה-AI המציא או פישל בשורות). עוברים שורה-שורה!
            print("⚠️ Full block not found. Falling back to line-by-line matching...")
            
            search_lines = [line.strip() for line in search_part.split('\n') if line.strip()]
            replace_lines = [line.strip() for line in replace_part.split('\n') if line.strip()]
            
            new_content = content
            changes_made = False
            
            for line in search_lines:
                found_line = None
                # בדיקה גמישה של השורה הנוכחית: כפי שהיא, או בהחלפת סוגי גרשיים
                if line in new_content:
                    found_line = line
                elif line.replace("'", '"') in new_content:
                    found_line = line.replace("'", '"')
                elif line.replace('"', "'") in new_content:
                    found_line = line.replace('"', "'")
                
                # אם מצאנו את השורה הזו בקובץ - נטפל בה
                if found_line:
                    # מחלצים את שורת ההחלפה המתאימה לפי האינדקס, אם אין - מחליפים בסטרינג ריק (מחיקה)
                    line_index = search_lines.index(line)
                    current_replace = replace_lines[line_index] if line_index < len(replace_lines) else ""
                    
                    new_content = new_content.replace(found_line, current_replace, 1)
                    changes_made = True
                else:
                    print(f"🔍 Line ignored (not found in file): {line}")

            # הגנת קצה קיצונית: אם אף שורה מהבלוק לא נמצאה בכל הקובץ, רק אז נחזיר שגיאה
            if not changes_made and replace_part != "":
                return (
                    f"Error: None of the lines in the SEARCH block were found in the file.\n"
                    f"AI tried to find lines from:\n{search_part}"
                )

        # 5. כתיבה סופית חזרה לדיסק
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("patch_test_code Successfully patched")
        return f"Successfully patched {file_path}."
    
    except Exception as e:
        return f"An error occurred during patching: {str(e)}"

# def patch_test_code(file_path: str, patch_content: str) -> str:
#     """
#     Applies a Search/Replace patch to a file using a safe path.
#     Format of patch_content:
#     <<<<<<< SEARCH
#     old code
#     =======
#     new code
#     >>>>>>> REPLACE
#     """
#     print(f"patch_test_code patch_content: {patch_content}")
#     try:
#         # שימוש בפונקציית העזר כדי לקבל נתיב בטוח ומלא
#         full_path = get_safe_full_path(REPO_PATH, file_path)
        
#         if not os.path.exists(full_path):
#             return f"Error: File {file_path} (Full path: {full_path}) not found."

#         with open(full_path, 'r', encoding='utf-8') as f:
#             content = f.read()

#         # חילוץ חלקי החיפוש וההחלפה מהפלט של ה-AI
#         if "<<<<<<< SEARCH" not in patch_content or "=======" not in patch_content:
#             return "Error: Invalid patch format. Missing <<<<<<< SEARCH or =======."

#         try:
#             search_part = patch_content.split("<<<<<<< SEARCH")[1].split("=======")[0].strip()
#             replace_part = patch_content.split("=======")[1].split(">>>>>>> REPLACE")[0].strip()
#         except IndexError:
#             return "Error: Could not parse SEARCH/REPLACE blocks. Check the format."

#         # בדיקה שהקוד לחיפוש אכן קיים בקובץ
#         if search_part not in content:
#             return "Error: The SEARCH block was not found in the file. Ensure the snippet matches EXACTLY (including indentation)."

#         # ביצוע ההחלפה
#         new_content = content.replace(search_part, replace_part)

#         with open(full_path, 'w', encoding='utf-8') as f:
#             f.write(new_content)

#         return f"Successfully patched {file_path}."
    
#     except Exception as e:
#         return f"An error occurred during patching: {str(e)}"

# @tool
# def patch_test_code(file_path: str, patch_content: str) -> str:
#     """
#     Applies a Search/Replace patch to a file using a safe path.
#     Format of patch_content:
#     <<<<<<< SEARCH
#     old code
#     =======
#     new code
#     >>>>>>> REPLACE
#     """
#     print(f"patch_test_code patch_content: {patch_content}")
#     try:
#         full_path = get_safe_full_path(REPO_PATH, file_path)
        
#         if not os.path.exists(full_path):
#             return f"Error: File {file_path} (Full path: {full_path}) not found."

#         with open(full_path, 'r', encoding='utf-8') as f:
#             content = f.read()

#         if "<<<<<<< SEARCH" not in patch_content or "=======" not in patch_content or ">>>>>>> REPLACE" not in patch_content:
#             return "Error: Invalid patch format. Missing <<<<<<< SEARCH, =======, or >>>>>>> REPLACE."

#         try:
#             # 🎯 התיקון: מנקים רק ירידות שורה עודפות שנוצרות מהתגיות, שומרים על הזחות (Indentation) קריטיות!
#             search_part = patch_content.split("<<<<<<< SEARCH")[1].split("=======")[0].strip('\r\n')
#             replace_part = patch_content.split("=======")[1].split(">>>>>>> REPLACE")[0].strip('\r\n')
#         except IndexError:
#             return "Error: Could not parse SEARCH/REPLACE blocks. Check the format."

#         # בדיקה שהקוד לחיפוש אכן קיים בקובץ
#         if search_part not in content:
#             return (
#                 "Error: The SEARCH block was not found in the file. "
#                 "Ensure the snippet matches EXACTLY, including all spaces and indentation."
#             )

#         # 🎯 התיקון: מבצעים החלפה של המופע הספציפי הראשון בלבד (count=1) כדי למנוע דריסת טסטים אחרים
#         new_content = content.replace(search_part, replace_part, 1)

#         with open(full_path, 'w', encoding='utf-8') as f:
#             f.write(new_content)

#         print("patch_test_code Successfully patched")
#         return f"Successfully patched {file_path}."
    
#     except Exception as e:
#         return f"An error occurred during patching: {str(e)}"
        

WRITER_TOOLS = [write_local_file, patch_test_code]    