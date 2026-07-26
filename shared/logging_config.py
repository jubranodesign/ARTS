import logging
import os
import sys


def _level_to_numeric(level: str) -> int:
    return getattr(logging, level.upper(), logging.INFO)


def configure_logging(level: str | None = None) -> None:
    """
    Configure root logging once per process (call from entry points after load_dotenv).

    If handlers already exist and ``level`` is None, the current root level is kept
    (so build_app and similar callers do not reset DEBUG set by an entry point).
    When ``level`` is None on first setup, uses LOG_LEVEL env or INFO.
    """
    root = logging.getLogger()
    if root.handlers:
        if level is not None:
            root.setLevel(_level_to_numeric(level))
        return

    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    numeric = _level_to_numeric(log_level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(numeric)
