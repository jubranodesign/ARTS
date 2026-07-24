import os
import re


def extract_python_path(text: str) -> str:
    """
    Extracts the first Python file path found in a string.
    Supports paths like: 'service/api.py', './tests/test_x.py', 'main.py'
    """
    if not text:
        return "unknown_file.py"

    pattern = r'([\w\d/_.-]+\.py)'
    match = re.search(pattern, text)

    if match:
        path = match.group(1)
        return path.strip().lstrip('./')

    return "unknown_file.py"


def normalize_relative_path(path: str, *, lowercase: bool = False) -> str:
    """Normalize repo-relative paths (forward slashes; optional lowercase for comparison)."""
    if not path:
        return ""
    normalized = path.replace("\\", "/").strip()
    return normalized.lower() if lowercase else normalized


def get_safe_full_path(base_path: str, relative_path: str) -> str:
    """
    מנקה נתיב שניתן על ידי ה-AI ומחבר אותו לנתיב הבסיס בצורה בטוחה.
    """
    if not relative_path:
        return ""

    clean_path = relative_path.strip().strip("'").strip('"')
    full_path = os.path.join(base_path, clean_path)
    return os.path.normpath(full_path)


def get_test_path(target_file: str) -> str:
    """
    ממיר נתיב של קובץ מקור לנתיב של קובץ טסט.
    דוגמה: scraper/api.py -> tests/scraper/test_api.py
    """
    clean_path = normalize_relative_path(target_file)

    parts = clean_path.split("/")
    folder = "/".join(parts[:-1])
    filename = parts[-1]

    if folder:
        return f"tests/{folder}/test_{filename}"
    return f"tests/test_{filename}"


def get_import_path(target_file: str) -> str:
    """
    Converts a file path (e.g., scraper_service/scraper_api.py)
    into a python import path (e.g., scraper_service.scraper_api).
    """
    if not target_file:
        return ""

    path_without_ext = os.path.splitext(normalize_relative_path(target_file))[0]
    import_path = path_without_ext.replace("/", ".")
    return import_path.strip(".")
