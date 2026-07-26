"""Backward compatibility — import from ``shared.paths`` instead."""

from shared.paths import (
    extract_python_path,
    get_import_path,
    get_safe_full_path,
    get_test_path,
    normalize_relative_path,
)

__all__ = [
    "extract_python_path",
    "get_import_path",
    "get_safe_full_path",
    "get_test_path",
    "normalize_relative_path",
]
