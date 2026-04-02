import re


def count_test_cases_from_list(plan_text: str) -> int:
    try:
        parts = re.split(r"(?i)^#+.*test cases.*$", plan_text, flags=re.MULTILINE)
        if len(parts) < 2:
            return 0

        cases_block = re.split(r"(?m)^#+", parts[1])[0]
        return len(re.findall(r"(?m)^\s*\d+\.\s+", cases_block))
    except Exception:
        return 0


def parse_architecture_summary(summary_text: str) -> dict:
    """
    מפרקת את ה-Summary המילולי לדיקשנרי לפי כותרות הסעיפים.
    עובדת על בסיס הפורמט הקבוע של ArchitectureSnapshot.
    """
    sections = {
        "component": r"Component:\s*(.*)",
        "file": r"File:\s*(.*)",
        "description": r"General Description:\s*(.*)",
        "logic": r"Technical Logic:\s*(.*)",
        "elements": r"Key Elements:\s*(.*)",
        "dependencies": r"Dependencies:\s*(.*)",
        "golden_example": r"--- REFERENCE TEST PATTERN \(Golden Example\) ---\n(.*?)(?=\n✅|\n---|$)"
    }
    
    parsed_data = {}
    
    for key, pattern in sections.items():
        # שימוש ב-re.DOTALL עבור ה-Golden Example כי הוא רב-שורתי
        flags = re.DOTALL if key == "golden_example" else 0
        match = re.search(pattern, summary_text, flags)
        
        if match:
            parsed_data[key] = match.group(1).strip()
        else:
            parsed_data[key] = None
            
    return parsed_data