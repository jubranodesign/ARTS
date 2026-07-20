# SHARED_LOGGING_RULES = """
# - Check if the source code uses standard print() statements or a logger.
# - If print(...), you MUST use pytest's native capsys fixture and assert against capsys.readouterr().out.
# - If logger, use caplog and assert against caplog.text.
# """

# SHARED_LOGGING_RULES = """- **INSPECT LOGGING VS PRINT**: Check if the source code uses standard `print()` statements or a `logger`.
# - **IF PRINT IS USED**: You MUST use pytest's native `capsys` fixture in the test arguments and assert against `capsys.readouterr().out`.
# - **IF LOGGER IS USED**: You MUST use pytest's native `caplog` fixture and assert against `caplog.text`.
# - **CRITICAL**: NEVER mock or patch `print` or `logger` directly. Always use the native fixtures mentioned above."""


SHARED_LOGGING_RULES = """- **INSPECT LOGGING VS PRINT**: Check if the source code uses standard `print()` statements or a `logger`.
- **IF PRINT IS USED**: You MUST use pytest's native `capsys` fixture.
- **CAPSYS SINGLE READ RULE**: `capsys.readouterr()` clears the buffer! ALWAYS assign it to a variable first (e.g., `captured = capsys.readouterr()`) and perform all assertions against `captured.out` or `captured.err`. NEVER call `readouterr()` twice in the same test function.
- **IF LOGGER IS USED**: You MUST use pytest's native `caplog` fixture and assert against `caplog.text`.
- **CRITICAL**: NEVER mock or patch `print` or `logger` directly."""