import os
import re
from langchain_core.messages import trim_messages


def get_clean_text(content):
    """
    Extracts plain text from LangChain message content.
    Handles both simple strings and Gemini's complex block format.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            block["text"] for block in content 
            if isinstance(block, dict) and "text" in block
        )
    return str(content)


def get_trimmed_messages(messages, llm, max_tokens=3000):
    """
    מקבלת רשימת הודעות ומחזירה אותן גזורות לפי המכסה המבוקשת.
    תמיד שומרת על הודעת ה-System.
    """
    trimmer = trim_messages(
        max_tokens=max_tokens,
        strategy="last",
        token_counter=llm,
        include_system=True,
        allow_partial=False
    )
    return trimmer.invoke(messages)


def extract_python_path(text: str) -> str:
    """
    Extracts the first Python file path found in a string.
    Supports paths like: 'service/api.py', './tests/test_x.py', 'main.py'
    """
    if not text:
        return "unknown_file.py"
        
    # Regex משופר שתופס נתיבים מורכבים יותר
    pattern = r'([\w\d/_.-]+\.py)'
    match = re.search(pattern, text)
    
    if match:
        path = match.group(1)
        # ניקוי תווים מיותרים אם נתפסו בסוף
        return path.strip().lstrip('./')
    
    return "unknown_file.py"

def count_test_cases_from_list(plan_text: str) -> int:
    try:
        # מחפש את החלק שמתחיל אחרי שורה שמכילה "Test Cases" (לא משנה כמה # יש שם)
        parts = re.split(r"(?i)^#+.*test cases.*$", plan_text, flags=re.MULTILINE)
        if len(parts) < 2: return 0
        
        # לוקח רק עד הכותרת הבאה (#)
        cases_block = re.split(r"(?m)^#+", parts[1])[0]
        
        # סופר שורות שמתחילות במספר (1. , 2. ...)
        return len(re.findall(r"(?m)^\s*\d+\.\s+", cases_block))
    except:
        return 0

def get_safe_full_path(base_path: str, relative_path: str) -> str:
    """
    מנקה נתיב שניתן על ידי ה-AI ומחבר אותו לנתיב הבסיס בצורה בטוחה.
    """
    if not relative_path:
        return ""
    
    # 1. ניקוי "לכלוך" מה-LLM (רווחים, גרשיים)
    clean_path = relative_path.strip().strip("'").strip('"')
    
    # 2. חיבור נתיבים - os.path.join מטפל בסלאשים לפי מערכת ההפעלה
    full_path = os.path.join(base_path, clean_path)
    
    # 3. נרמול (מחיקת סלאשים כפולים, נקודות מיותרות וכו')
    return os.path.normpath(full_path)


def get_test_path(target_file: str) -> str:
    """
    ממיר נתיב של קובץ מקור לנתיב של קובץ טסט.
    דוגמה: scraper/api.py -> tests/scraper/test_api.py
    """
    # ניקוי נתיבים (החלפת סלאשים של ווינדוס במידת הצורך)
    clean_path = target_file.replace("\\", "/")
    
    parts = clean_path.split("/")
    folder = "/".join(parts[:-1])
    filename = parts[-1]
    
    # בניית הנתיב החדש
    if folder:
        return f"tests/{folder}/test_{filename}"
    return f"tests/test_{filename}"