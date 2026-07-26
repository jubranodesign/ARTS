def log_tail(text: str, *, max_chars: int = 2000, max_lines: int = 30) -> str:
    """Truncate long text for debug logging."""
    if not text:
        return ""
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
        text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[-max_chars:]
    return text
