FIX_PROMPT_REGISTRY = {
    "ModuleNotFoundError": """
    ### MANDATORY REPAIR INSTRUCTION:
    The test suite failed during collection because an internal module import path could not be resolved.
    - Do NOT touch the source code imports.
    - Fix system path mismatches (`sys.path.insert`) or missing import setup at the top of the file.
    """,
    "AssertionError_rollback": """
    ### MANDATORY REPAIR INSTRUCTION:
    A database transaction test failed because a `rollback()` call was expected but never triggered.
    - Check if the error originates from the source code missing a `session.rollback()` inside its database `except` block.
    - If the source code handles it correctly but the mock doesn't reflect it, ensure your test fixture chains `mock_cm.return_value.__enter__.return_value = mock_session` properly.
    """,
    "AssertionError_capsys": """
    ### MANDATORY REPAIR INSTRUCTION:
    A log or print assertion failed. 
    - Check if `print()` output was captured in `captured.out` instead of `captured.err`.
    - Ensure the test function arguments use `capsys` instead of `caplog` when testing code with `print()`.
    - Always isolate output via `captured = capsys.readouterr()`.
    - Assert `captured.out` for standard prints and `captured.err` ONLY if `print(..., file=sys.stderr)` was explicitly used.
    """,
    "General_Exception": """
    ### MANDATORY REPAIR INSTRUCTION:
    Review the Pytest traceback carefully. Identify the exact failing line or assertion and apply a precise logical patch.
    """,
    "SyntaxError_Indentation": """
    ### MANDATORY REPAIR INSTRUCTION:
    The Python file failed during collection because of an IndentationError or SyntaxError caused by a previous patch.
    - Inspect the exact line mentioned in the traceback.
    - Make sure the indentation (spaces/tabs) inside your SEARCH and REPLACE blocks MATCHES the surrounding function body exactly.
    - Apply a clean `patch_test_code` or rewrite the broken function with correct 4-space Python indentation.
    """
}


def analyze_test_failure(logs: str, root_package: str, import_path: str) -> str:
    """Utility function to parse traceback and return targeted repair instructions."""

    # 🛑 0. טיפול מוקדם בשגיאות סינטקס/הזחה שנוצרו מהפאתץ'
    if "IndentationError" in logs or "SyntaxError" in logs:
        return FIX_PROMPT_REGISTRY["SyntaxError_Indentation"]
        
    # --- 1. ModuleNotFoundError Handling ---
    if "ModuleNotFoundError" in logs:
        import_crash_hint = ""
        # דיאגנוזה ממוקדת לפעולה בלבד - בלי לחזור על חוק ה-Blanket Mock הגלובלי
        if root_package and root_package in logs:
            import_crash_hint = (
                f"\n🚨 SPECIFIC DIAGNOSIS: The ModuleNotFoundError is caused BECAUSE you blocked '{root_package}' in sys.modules!\n"
                f"You MUST create a SEARCH/REPLACE block to DELETE any lines assigning `sys.modules['{root_package}']` or `sys.modules['{import_path}']` from the top of the file immediately!\n"
            )

        base_instruction = FIX_PROMPT_REGISTRY["ModuleNotFoundError"]
        return f"{base_instruction}\n{import_crash_hint}"

    # --- 2. Database Rollback Failure ---
    elif "rollback" in logs and "AssertionError" in logs:
        return FIX_PROMPT_REGISTRY["AssertionError_rollback"]

    # --- 3. Print / Capsys / Stream Mismatch ---
    elif "capsys" in logs or "readouterr" in logs or "CaptureResult" in logs:
        return FIX_PROMPT_REGISTRY["AssertionError_capsys"]

    # --- 4. Fallback ---
    return FIX_PROMPT_REGISTRY["General_Exception"]