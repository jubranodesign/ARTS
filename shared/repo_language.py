"""Repo language hooks (default: python). Other values log a warning and fall back."""

from __future__ import annotations

import logging
import os

from langchain_text_splitters import Language

logger = logging.getLogger(__name__)

DEFAULT_REPO_LANGUAGE = "python"
SUPPORTED_REPO_LANGUAGES: frozenset[str] = frozenset({DEFAULT_REPO_LANGUAGE})

PYTHON_CHUNK_SIZE = 1000
PYTHON_CHUNK_OVERLAP = 150


def resolve_repo_language() -> str:
    """Value from REPO_LANGUAGE env (normalized), default python."""
    raw = os.getenv("REPO_LANGUAGE")
    if not raw or not str(raw).strip():
        return DEFAULT_REPO_LANGUAGE
    return str(raw).strip().lower()


def effective_repo_language() -> str:
    """Language used at runtime; unsupported values fall back to python."""
    requested = resolve_repo_language()
    if requested in SUPPORTED_REPO_LANGUAGES:
        return requested
    logger.warning(
        "REPO_LANGUAGE=%r is not supported yet; using %r for ingest and test execution.",
        requested,
        DEFAULT_REPO_LANGUAGE,
    )
    return DEFAULT_REPO_LANGUAGE


def get_splitter_kwargs(language: str | None = None) -> dict:
    """Arguments for RecursiveCharacterTextSplitter.from_language (python today)."""
    lang = language or effective_repo_language()
    if lang != DEFAULT_REPO_LANGUAGE:
        lang = effective_repo_language()
    if lang == DEFAULT_REPO_LANGUAGE:
        return {
            "language": Language.PYTHON,
            "chunk_size": PYTHON_CHUNK_SIZE,
            "chunk_overlap": PYTHON_CHUNK_OVERLAP,
        }
    raise RuntimeError(f"Unhandled repo language: {lang!r}")
