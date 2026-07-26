"""LangGraph ``config[\"configurable\"]`` contract (keys, merge, validation)."""

from __future__ import annotations

from typing import TypedDict

from services.code_processor import CodeProcessor
from services.vector_db_service import VectorDBService
from shared.run_policy import get_default_model_provider

# Override via run_local GRAPH_CONFIG or main ``configurable=`` — not env.
GRAPH_CONFIG_OVERRIDE_KEYS: frozenset[str] = frozenset(
    {
        "thread_id",
        "model_provider",
    }
)

# Injected by build_langgraph_run_config; callers pass as function args, not GRAPH_CONFIG.
GRAPH_CONFIG_INJECTED_KEYS: frozenset[str] = frozenset(
    {
        "repo_path",
        "vdb",
        "processor",
    }
)

GRAPH_CONFIG_ALL_KEYS: frozenset[str] = (
    GRAPH_CONFIG_OVERRIDE_KEYS | GRAPH_CONFIG_INJECTED_KEYS
)

DEFAULT_THREAD_ID = "test_session_001"


class GraphConfigurable(TypedDict):
    """Runtime dict passed to LangGraph nodes and tools."""

    thread_id: str
    model_provider: str
    repo_path: str
    vdb: VectorDBService
    processor: CodeProcessor


def _validate_graph_configurable(merged: dict) -> None:
    missing = [k for k in GRAPH_CONFIG_ALL_KEYS if k not in merged or merged[k] is None]
    if missing:
        raise ValueError(
            f"Graph configurable missing required keys: {missing}. "
            f"Expected keys: {sorted(GRAPH_CONFIG_ALL_KEYS)}"
        )
    if not isinstance(merged["repo_path"], str) or not str(merged["repo_path"]).strip():
        raise ValueError("configurable['repo_path'] must be a non-empty string")
    if not isinstance(merged["thread_id"], str) or not str(merged["thread_id"]).strip():
        raise ValueError("configurable['thread_id'] must be a non-empty string")


def merge_graph_configurable(
    repo_path: str,
    vdb: VectorDBService,
    processor: CodeProcessor,
    *,
    overrides: dict | None = None,
) -> GraphConfigurable:
    """
    Build the configurable payload for a graph run.

    ``overrides`` may only contain keys in GRAPH_CONFIG_OVERRIDE_KEYS.
    Policy (RISK_THRESHOLD, MAX_TEST_ATTEMPTS) is read from env via shared.run_policy, not here.
    """
    merged: dict = {
        "thread_id": DEFAULT_THREAD_ID,
        "model_provider": get_default_model_provider(),
    }

    if overrides:
        unknown = set(overrides) - GRAPH_CONFIG_OVERRIDE_KEYS
        if unknown:
            raise ValueError(
                f"Unknown GRAPH_CONFIG keys: {sorted(unknown)}. "
                f"Allowed overrides: {sorted(GRAPH_CONFIG_OVERRIDE_KEYS)}. "
                "Policy settings use env (RISK_THRESHOLD, MAX_TEST_ATTEMPTS, MODEL_PROVIDER). "
                "repo_path / vdb / processor are set by run_* entrypoints, not GRAPH_CONFIG."
            )
        merged.update({k: overrides[k] for k in GRAPH_CONFIG_OVERRIDE_KEYS if k in overrides})

    merged["repo_path"] = repo_path
    merged["vdb"] = vdb
    merged["processor"] = processor

    _validate_graph_configurable(merged)
    return merged  # type: ignore[return-value]


def build_langgraph_run_config(
    repo_path: str,
    vdb: VectorDBService,
    processor: CodeProcessor,
    *,
    overrides: dict | None = None,
) -> dict:
    """Return ``{\"configurable\": ...}`` for LangGraph invoke/stream."""
    return {"configurable": merge_graph_configurable(repo_path, vdb, processor, overrides=overrides)}
