"""Lightweight pre-flight checks before agent/ingest runs (OSS-friendly)."""

from __future__ import annotations

import logging
import os

from shared.run_policy import get_default_model_provider

logger = logging.getLogger(__name__)

_PROVIDER_ENV_KEYS: dict[str, tuple[str, ...]] = {
    "mistral": ("MISTRAL_API_KEY",),
    "groq": ("GROQ_API_KEY",),
    "gemini": ("GOOGLE_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "open_router": ("OPENROUTER_API_KEY",),
    "github": ("OPENAI_API_KEY", "GITHUB_TOKEN"),
    # ollama: local daemon — no cloud key
}


def _env_set(name: str) -> bool:
    val = os.getenv(name)
    return bool(val and str(val).strip())


def check_repo_path_exists(repo_path: str) -> None:
    if not repo_path or not str(repo_path).strip():
        raise RuntimeError("REPO_PATH is empty.")
    path = os.path.abspath(os.path.expanduser(repo_path.strip()))
    if not os.path.isdir(path):
        raise RuntimeError(
            f"REPO_PATH is not a directory: {path!r}. "
            "Set REPO_PATH in .env to the repository you want to test."
        )


def check_llm_provider_configured(provider: str | None = None) -> None:
    name = (provider or get_default_model_provider()).lower()
    if name == "ollama":
        return
    keys = _PROVIDER_ENV_KEYS.get(name)
    if not keys:
        raise RuntimeError(
            f"Unknown MODEL_PROVIDER {name!r}. "
            f"Supported: {sorted(_PROVIDER_ENV_KEYS)} and ollama."
        )
    if any(_env_set(k) for k in keys):
        return
    hint = " or ".join(keys)
    raise RuntimeError(
        f"MODEL_PROVIDER is {name!r} but no API key found in env ({hint}). "
        "Set the key in .env or change MODEL_PROVIDER."
    )


def warn_if_vector_store_empty() -> None:
    """Log a warning when Chroma has no documents (ingest not run yet)."""
    try:
        from services.vector_db_service import VectorDBService

        vdb = VectorDBService()
        count = vdb.db._collection.count()
    except Exception as exc:
        logger.warning(
            "Could not inspect vector store (ingest may be required): %s",
            exc,
        )
        return
    if count == 0:
        logger.warning(
            "Vector store is empty (0 chunks). Run ingest before the agent, e.g. "
            "'python ingest.py --repo-path <REPO_PATH> --both'. "
            "Researcher retrieval will be weak until then."
        )


def validate_runtime_startup(
    repo_path: str,
    *,
    warn_empty_vdb: bool = True,
    graph_overrides: dict | None = None,
) -> None:
    """Fail fast on missing repo or LLM keys; optional warning for empty Chroma."""
    from shared.agent_llm_policy import resolved_graph_model_providers

    check_repo_path_exists(repo_path)
    # Approximate configurable overrides for provider resolution (no vdb/processor needed).
    cfg: dict = {
        "model_provider": get_default_model_provider(),
        "model_providers": {},
    }
    if graph_overrides:
        if "model_provider" in graph_overrides:
            cfg["model_provider"] = graph_overrides["model_provider"]
        if "model_providers" in graph_overrides:
            cfg["model_providers"] = graph_overrides["model_providers"]
    for provider in resolved_graph_model_providers(cfg):
        check_llm_provider_configured(provider)
    if warn_empty_vdb:
        warn_if_vector_store_empty()
