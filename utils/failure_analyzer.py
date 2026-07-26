import logging

from utils.log_format import log_tail

logger = logging.getLogger(__name__)

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
    logger.debug(
        "analyze_test_failure logs_len=%s root_package=%r import_path=%r",
        len(logs or ""),
        root_package,
        import_path,
    )
    logger.debug("analyze_test_failure logs tail:\n%s", log_tail(logs))

    if "IndentationError" in logs or "SyntaxError" in logs:
        logger.debug("analyze_test_failure matched rule: SyntaxError_Indentation")
        return FIX_PROMPT_REGISTRY["SyntaxError_Indentation"]

    if "ModuleNotFoundError" in logs:
        import_crash_hint = ""
        if root_package and root_package in logs:
            import_crash_hint = (
                f"\n🚨 SPECIFIC DIAGNOSIS: The ModuleNotFoundError is caused BECAUSE you blocked '{root_package}' in sys.modules!\n"
                f"You MUST create a SEARCH/REPLACE block to DELETE any lines assigning `sys.modules['{root_package}']` or `sys.modules['{import_path}']` from the top of the file immediately!\n"
            )
            logger.debug(
                "analyze_test_failure ModuleNotFoundError with sys.modules hint for %r",
                root_package,
            )
        else:
            logger.debug("analyze_test_failure matched rule: ModuleNotFoundError (base)")

        base_instruction = FIX_PROMPT_REGISTRY["ModuleNotFoundError"]
        result = f"{base_instruction}\n{import_crash_hint}"
        logger.debug(
            "analyze_test_failure instruction_len=%s",
            len(result),
        )
        return result

    if "rollback" in logs and "AssertionError" in logs:
        logger.debug("analyze_test_failure matched rule: AssertionError_rollback")
        return FIX_PROMPT_REGISTRY["AssertionError_rollback"]

    if "capsys" in logs or "readouterr" in logs or "CaptureResult" in logs:
        logger.debug("analyze_test_failure matched rule: AssertionError_capsys")
        return FIX_PROMPT_REGISTRY["AssertionError_capsys"]

    logger.debug("analyze_test_failure matched rule: General_Exception")
    return FIX_PROMPT_REGISTRY["General_Exception"]
