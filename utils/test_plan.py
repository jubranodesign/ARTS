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
