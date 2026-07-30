"""Repo language hooks: splitter via langchain Language; full pipeline python-only today."""

from __future__ import annotations

import logging
import os

from langchain_text_splitters import Language

logger = logging.getLogger(__name__)

DEFAULT_REPO_LANGUAGE = "python"

# End-to-end ARTS (scanner, pytest, prompts, risk gate) — not the same as splitter support.
ARTS_FULLY_SUPPORTED_LANGUAGES: frozenset[str] = frozenset({DEFAULT_REPO_LANGUAGE})

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150

# Env aliases → Language.name (lowercase), e.g. REPO_LANGUAGE=typescript
_REPO_LANGUAGE_ALIASES: dict[str, str] = {
    "typescript": "ts",
    "javascript": "js",
    "c#": "csharp",
    "c-sharp": "csharp",
    "cpp": "cpp",
    "c++": "cpp",
    "golang": "go",
    "vb6": "visualbasic6",
    "visualbasic": "visualbasic6",
}

_LANGUAGE_BY_NAME: dict[str, Language] = {lang.name.lower(): lang for lang in Language}

# IDs accepted for ingest splitting (enum names + common aliases).
SPLITTER_LANGUAGE_IDS: frozenset[str] = frozenset(_LANGUAGE_BY_NAME.keys()) | frozenset(
    _REPO_LANGUAGE_ALIASES.keys()
)


def resolve_repo_language() -> str:
    """Value from REPO_LANGUAGE env (normalized), default python."""
    raw = os.getenv("REPO_LANGUAGE")
    if not raw or not str(raw).strip():
        return DEFAULT_REPO_LANGUAGE
    return str(raw).strip().lower()


def _normalize_language_id(name: str) -> str:
    key = name.strip().lower()
    return _REPO_LANGUAGE_ALIASES.get(key, key)


def repo_language_to_splitter_language(name: str) -> Language | None:
    """Map REPO_LANGUAGE string to langchain Language, or None if unknown."""
    canonical = _normalize_language_id(name)
    return _LANGUAGE_BY_NAME.get(canonical)


def is_splitter_language_supported(name: str) -> bool:
    key = name.strip().lower()
    if key in _REPO_LANGUAGE_ALIASES or key in _LANGUAGE_BY_NAME:
        return repo_language_to_splitter_language(key) is not None
    return False


def effective_splitter_language_id() -> str:
    """Language id used for RecursiveCharacterTextSplitter.from_language."""
    requested = resolve_repo_language()
    lang = repo_language_to_splitter_language(requested)
    if lang is not None:
        return lang.name.lower()
    logger.warning(
        "REPO_LANGUAGE=%r is not a known Language splitter id; using %r.",
        requested,
        DEFAULT_REPO_LANGUAGE,
    )
    return DEFAULT_REPO_LANGUAGE


def effective_repo_language() -> str:
    """Language used for test execution and pipeline defaults (python-only today)."""
    requested = resolve_repo_language()
    if requested in ARTS_FULLY_SUPPORTED_LANGUAGES or _normalize_language_id(
        requested
    ) in ARTS_FULLY_SUPPORTED_LANGUAGES:
        return DEFAULT_REPO_LANGUAGE

    if repo_language_to_splitter_language(requested) is not None:
        logger.warning(
            "REPO_LANGUAGE=%r: ingest splitter is supported, but the full ARTS "
            "pipeline (scanner, pytest, prompts) still runs as %r.",
            requested,
            DEFAULT_REPO_LANGUAGE,
        )
        return DEFAULT_REPO_LANGUAGE

    logger.warning(
        "REPO_LANGUAGE=%r is not supported; using %r for ingest splitter and pipeline.",
        requested,
        DEFAULT_REPO_LANGUAGE,
    )
    return DEFAULT_REPO_LANGUAGE


def get_splitter_kwargs(language: str | None = None) -> dict:
    """Arguments for RecursiveCharacterTextSplitter.from_language."""
    requested = language if language is not None else resolve_repo_language()
    lang_enum = repo_language_to_splitter_language(requested)
    if lang_enum is None:
        logger.warning(
            "No Language mapping for REPO_LANGUAGE=%r; using python splitter.",
            requested,
        )
        lang_enum = Language.PYTHON
    return {
        "language": lang_enum,
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "chunk_overlap": DEFAULT_CHUNK_OVERLAP,
    }


# Back-compat name used in docs
SUPPORTED_REPO_LANGUAGES = ARTS_FULLY_SUPPORTED_LANGUAGES


def get_chunk_summary_prompt() -> str:
    """Ingest prompt for production source chunks (generic until per-language overrides)."""
    from shared.ingestion_prompts import CHUNK_SUMMARY_PROMPT

    return CHUNK_SUMMARY_PROMPT


def get_seed_summary_prompt() -> str:
    """Ingest prompt for golden test seed chunks (generic until per-language overrides)."""
    from shared.ingestion_prompts import SEED_SUMMARY_PROMPT

    return SEED_SUMMARY_PROMPT


def get_bm25_preprocess_func():
    """BM25 preprocess for source ingest (generic default; python tokenizer optional later)."""
    from utils.retrieval import generic_code_tokenizer

    return generic_code_tokenizer
