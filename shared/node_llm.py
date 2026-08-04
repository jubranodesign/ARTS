import logging

from shared.agent_llm_policy import resolve_model_provider_for_node
from shared.llm_factory import get_model

logger = logging.getLogger(__name__)


def setup_node_llm(config, tools=None, *, node_id: str | None = None):
    """Resolve provider for node_id, initialize LLM, optionally bind tools."""
    configurable = config.get("configurable", {})
    if node_id:
        provider = resolve_model_provider_for_node(node_id, configurable)
    else:
        from shared.run_policy import get_default_model_provider

        provider = configurable.get("model_provider") or get_default_model_provider()

    logger.debug("setup_node_llm node=%s provider=%s", node_id, provider)

    llm = get_model(provider)

    if tools:
        return llm.bind_tools(tools)

    return llm
