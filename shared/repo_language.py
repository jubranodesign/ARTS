"""Repo language hooks: ingest, paths, prompts, and BM25 keyed to REPO_LANGUAGE."""

from __future__ import annotations

import logging
import os

from langchain_text_splitters import Language

logger = logging.getLogger(__name__)

DEFAULT_REPO_LANGUAGE = "python"

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

# File suffixes for ingest scanner, keyed by Language.name (lowercase).
_EXTENSIONS_BY_LANGUAGE_ID: dict[str, frozenset[str]] = {
    "c": frozenset({".c", ".h"}),
    "cpp": frozenset({".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h"}),
    "csharp": frozenset({".cs"}),
    "cobol": frozenset({".cob", ".cbl", ".cpy"}),
    "elixir": frozenset({".ex", ".exs"}),
    "go": frozenset({".go"}),
    "haskell": frozenset({".hs", ".lhs"}),
    "html": frozenset({".html", ".htm"}),
    "java": frozenset({".java"}),
    "js": frozenset({".js", ".mjs", ".cjs"}),
    "kotlin": frozenset({".kt", ".kts"}),
    "latex": frozenset({".tex", ".latex"}),
    "lua": frozenset({".lua"}),
    "markdown": frozenset({".md", ".markdown"}),
    "perl": frozenset({".pl", ".pm"}),
    "php": frozenset({".php"}),
    "powershell": frozenset({".ps1", ".psm1", ".psd1"}),
    "proto": frozenset({".proto"}),
    "python": frozenset({".py"}),
    "r": frozenset({".r", ".R"}),
    "rst": frozenset({".rst"}),
    "ruby": frozenset({".rb"}),
    "rust": frozenset({".rs"}),
    "scala": frozenset({".scala", ".sc"}),
    "sol": frozenset({".sol"}),
    "swift": frozenset({".swift"}),
    "ts": frozenset({".ts", ".tsx"}),
    "visualbasic6": frozenset({".bas", ".frm", ".cls", ".vb"}),
}

# Repo docs on source ingest (not used when REPO_LANGUAGE=markdown — already in map).
_INGEST_SOURCE_DOC_EXTENSIONS: frozenset[str] = frozenset({".md"})

for _lang in Language:
    _lid = _lang.name.lower()
    if _lid not in _EXTENSIONS_BY_LANGUAGE_ID:
        logger.warning("No ingest file extensions mapped for Language.%s", _lang.name)

# Pipeline + ingest for Language ids with extensions map; non-Python runs need ARTS_TEST_RUNNER or .arts/runner.py.
ARTS_FULLY_SUPPORTED_LANGUAGES: frozenset[str] = frozenset(_EXTENSIONS_BY_LANGUAGE_ID.keys())


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
    """Language id for pipeline paths, prompts, and ingest (matches splitter id)."""
    return effective_splitter_language_id()


def is_python_pipeline() -> bool:
    return effective_splitter_language_id() == DEFAULT_REPO_LANGUAGE


def get_ingest_code_extensions() -> frozenset[str]:
    """Source/seed code suffixes for REPO_LANGUAGE (excludes doc-only .md)."""
    lang_id = effective_splitter_language_id()
    return _EXTENSIONS_BY_LANGUAGE_ID.get(
        lang_id, _EXTENSIONS_BY_LANGUAGE_ID[DEFAULT_REPO_LANGUAGE]
    )


def unknown_target_file_placeholder() -> str:
    ext = next(iter(get_ingest_code_extensions()), ".py")
    return f"unknown_file{ext}"


def resolve_test_framework() -> str:
    """Display framework for prompts; override with ARTS_TEST_FRAMEWORK."""
    raw = os.getenv("ARTS_TEST_FRAMEWORK")
    if raw and str(raw).strip():
        return str(raw).strip()
    if is_python_pipeline():
        return "pytest"
    return "use the framework shown in golden seed examples"


def get_writer_prompt_template() -> str:
    if is_python_pipeline():
        from agents.writer_agent.prompts import WRITER_PROMPT_TEMPLATE

        return WRITER_PROMPT_TEMPLATE
    from shared.agent_prompts import WRITER_PROMPT_GENERIC

    return WRITER_PROMPT_GENERIC


def get_repair_prompt_template() -> str:
    if is_python_pipeline():
        from agents.writer_agent.prompts import REPAIR_PROMPT_TEMPLATE

        return REPAIR_PROMPT_TEMPLATE
    from shared.agent_prompts import REPAIR_PROMPT_GENERIC

    return REPAIR_PROMPT_GENERIC


def get_designer_prompt_template() -> str:
    if is_python_pipeline():
        from agents.designer_agent.prompts import DESIGNER_PROMPT_TEMPLATE

        return DESIGNER_PROMPT_TEMPLATE
    from shared.agent_prompts import DESIGNER_PROMPT_GENERIC

    return DESIGNER_PROMPT_GENERIC


def get_reviewer_prompt_template() -> str:
    if is_python_pipeline():
        from agents.designer_agent.prompts import REVIEWER_PROMPT_TEMPLATE

        return REVIEWER_PROMPT_TEMPLATE
    from shared.agent_prompts import REVIEWER_PROMPT_GENERIC

    return REVIEWER_PROMPT_GENERIC


def get_architect_summary_prompt_template() -> str:
    if is_python_pipeline():
        from agents.researcher_agent.prompts import ARCHITECT_SUMMARY_PROMPT

        return ARCHITECT_SUMMARY_PROMPT
    from shared.agent_prompts import ARCHITECT_SUMMARY_PROMPT_GENERIC

    return ARCHITECT_SUMMARY_PROMPT_GENERIC


def writer_import_path_section(import_path: str) -> str:
    if not import_path or not is_python_pipeline():
        return ""
    return (
        f"\n5. **TARGET IMPORT**: Use absolute import path for code under test: "
        f"`from {import_path} import ...`.\n"
    )


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
    """BM25 preprocess keyed to REPO_LANGUAGE (via effective_splitter_language_id)."""
    from utils.retrieval import generic_code_tokenizer, python_code_tokenizer

    lang_id = effective_splitter_language_id()
    if lang_id == DEFAULT_REPO_LANGUAGE:
        return python_code_tokenizer
    return generic_code_tokenizer


def get_ingest_allowed_extensions(*, is_test: bool = False) -> set[str]:
    """
    Scanner suffixes for ingest, aligned with REPO_LANGUAGE splitter id.
    Seed uses the same code extensions as source; source may also include .md docs.
    """
    allowed = set(get_ingest_code_extensions())
    if not is_test and effective_splitter_language_id() != "markdown":
        allowed |= _INGEST_SOURCE_DOC_EXTENSIONS
    return allowed
