"""Per-agent LLM provider resolution (env + LangGraph configurable)."""

from __future__ import annotations

import os

from shared.run_policy import get_default_model_provider

# Graph nodes that call setup_node_llm
GRAPH_LLM_NODE_IDS: frozenset[str] = frozenset(
    {"researcher", "summarizer", "designer", "reviewer", "writer"}
)

_NODE_ENV_KEYS: dict[str, str] = {
    "researcher": "RESEARCHER_MODEL_PROVIDER",
    "summarizer": "SUMMARIZER_MODEL_PROVIDER",
    "designer": "DESIGNER_MODEL_PROVIDER",
    "reviewer": "REVIEWER_MODEL_PROVIDER",
    "writer": "WRITER_MODEL_PROVIDER",
}


def _provider_from_env(node_id: str) -> str | None:
    env_name = _NODE_ENV_KEYS.get(node_id)
    if not env_name:
        return None
    raw = os.getenv(env_name)
    if raw and str(raw).strip():
        return str(raw).strip().lower()
    return None


def resolve_model_provider_for_node(node_id: str, configurable: dict | None) -> str:
    """
    Provider for a graph node. Precedence:
    configurable['model_providers'][node_id] → {NODE}_MODEL_PROVIDER env
    → configurable['model_provider'] → MODEL_PROVIDER env default.
    """
    cfg = configurable or {}
    per_node = cfg.get("model_providers") or {}
    if isinstance(per_node, dict):
        override = per_node.get(node_id)
        if override and str(override).strip():
            return str(override).strip().lower()

    from_env = _provider_from_env(node_id)
    if from_env:
        return from_env

    global_cfg = cfg.get("model_provider")
    if global_cfg and str(global_cfg).strip():
        return str(global_cfg).strip().lower()

    return get_default_model_provider()


def resolved_graph_model_providers(configurable: dict | None) -> set[str]:
    """All providers that will be used in one graph run (for API key checks)."""
    cfg = configurable or {}
    return {
        resolve_model_provider_for_node(node_id, cfg) for node_id in GRAPH_LLM_NODE_IDS
    }
